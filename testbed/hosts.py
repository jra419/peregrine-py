#!/usr/bin/env python3

import subprocess
import time
import os

SCRIPT_DIR             = os.path.dirname(os.path.realpath(__file__))

CONTROLLER_EXE_NAME    = 'peregrine-controller'
ENGINE_EXE_NAME        = 'engine'
KITNET_EXE_NAME        = 'python' # oof

CONTROLLER_LOG_FILE    = '/tmp/run-with-hw.log'
CONTROLLER_READY_MSG   = 'Peregrine controller is ready.'
CONTROLLER_REPORT_FILE = 'peregrine-controller.tsv'

ENGINE_LOG_FILE        = '/tmp/engine.log'
ENGINE_READY_MSG       = 'Listening interface'
ENGINE_REPORT_FILE     = 'peregrine-engine.tsv'

KITNET_LOG_FILE        = '/tmp/kitnet.log'
KITNET_READY_MSG       = 'Listening on'

BIND_KERNEL_SCRIPT     = '/home/fcp/bind-e810-kernel.sh'
BIND_DPDK_SCRIPT       = '/home/fcp/bind-igb_uio.sh'

ENGINE_LISTEN_IFACE    = 'enp216s0f1'
TG_KERNEL_OUT_IFACE    = 'enp175s0f1'

TOFINO_WAITING_PERIOD  = 10 # seconds

class Host:
	def __init__(self, name, hostname, verbose=True):
		self.name = name
		self.hostname = hostname
		self.verbose = verbose
		self.test_connection()

	def exec(self, cmd, path=None, silence=False, background=False,
			must_succeed=True, capture_output=False):
		assert(type(cmd) == str)

		if self.verbose:
			self.log(f'exec \"{cmd}\"')

		remote_cmd = [
			'source ~/.bashrc',
			'source ~/.profile',
		]

		if path:
			remote_cmd.append(f'cd {path}')
		
		remote_cmd.append(cmd)
		remote_cmd = " && ".join(remote_cmd)

		ssh_flags = [ '-o', 'PasswordAuthentication=no', '-t' ]

		if background:
			ssh_flags.append('-f')
		
		cmd = [ 'ssh' ] + ssh_flags + [ self.hostname, remote_cmd ]

		if silence or capture_output:
			proc = subprocess.run(cmd, capture_output=True, text=True)
		else:
			stdout = subprocess.DEVNULL if background else None
			stderr = subprocess.DEVNULL if background else None
			proc = subprocess.run(cmd, stdout=stdout, stderr=stderr)

		if not background and must_succeed and proc.returncode != 0:
			self.log(f'Command failed.')
			self.log(f'  command:  \"{" ".join(cmd)}\"')
			self.log(f'  ret code: {proc.returncode}')

			if silence or capture_output:
				self.log('  stdout:')
				print(proc.stdout)

				self.log('  stderr:')
				print(proc.stderr)

			exit(1)

		out = proc.stdout if capture_output else None
		err = proc.stderr if capture_output else None

		return proc.returncode, out, err
	
	def test_connection(self):
		ret, _, _ = self.exec('hostname', silence=True, must_succeed=False)

		if ret != 0:
			self.log(f'ERROR: connection with host {self.hostname} failed. Exiting.')
			exit(1)
	
	def send_files(self, src, dst):
		cmd = [ 'rsync', '-avz', '--progress', src, f'{self.hostname}:{dst}' ]
		proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

		if proc.returncode != 0:
			self.log(f'Command failed (ret={proc.returncode}).')
			exit(1)
	
	def get_files(self, src, dst=SCRIPT_DIR):
		cmd = [ 'rsync', '-avz', '--progress', f'{self.hostname}:{src}', dst ]
		proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		target = f'{dst}/{src.split("/")[-1]}'
		
		if proc.returncode != 0:
			self.log(f'Command failed (ret={proc.returncode}).')
			exit(1)
		
		return target
	
	def has_directory(self, directory):
		cmd = f'test -d {directory}'
		code, _, _ = self.exec(cmd, silence=True, must_succeed=False)
		return code == 0
	
	def kill(self, program_name):
		cmd = f'sudo killall {program_name} || true'
		self.exec(cmd, silence=True, must_succeed=False)
	
	def is_program_running(self, path_to_executable):
		testing_prog = f'ps -A  -o pid,args | grep {path_to_executable}'
		_, stdout, _ = self.exec(testing_prog, silence=True, capture_output=True, must_succeed=False)
		num_matches = len(list(filter(None, stdout.split('\n'))))

		# at least 3 because:
		#  1 for the ps program
		#  1 for the grep program
		#  1 for the actual program
		#  (maybe one additionally for the sudo program, or a mother script)
		return num_matches >= 3
	
	def log(self, msg):
		print(f'[{self.name}] {msg}')
	
	def err(self, msg):
		print(f'[{self.name}] ERROR: {msg}')
		exit(1)

class Tofino(Host):
	def __init__(self, hostname, peregrine_path, verbose=True):
		super().__init__('tofino', hostname, verbose)

		self.peregrine_path = peregrine_path
		self.controller_path = f'{self.peregrine_path}/controller'
		self.p4_path =  f'{self.peregrine_path}/p4'
		self.controller_exe_path = f'{self.controller_path}/build/{CONTROLLER_EXE_NAME}'

		if not self.has_directory(self.peregrine_path):
			self.err(f'Directory not found: {self.peregrine_path}')

		if not self.has_directory(self.controller_path):
			self.err(f'Directory not found: {self.controller_path}')

		if not self.has_directory(self.p4_path):
			self.err(f'Directory not found: {self.p4_path}')

		# Stop any instances running before running our own
		self.stop()
	
	def install(self):
		self.exec('make install', path=self.p4_path, silence=True)
	
	def start(self):
		# Compiling first
		self.exec('make release -j', path=self.controller_path, silence=True)

		self.exec(f'./run-with-hw.sh > {CONTROLLER_LOG_FILE} 2>&1',
			path=self.controller_path, background=True)
		
		while 1:
			time.sleep(1)

			ret, out, err = self.exec(f'cat {CONTROLLER_LOG_FILE}', capture_output=True)

			if not self.is_program_running(self.controller_exe_path):
				self.log('ERROR: Controller not running.')
				self.log('Dumping of log file:')
				print(out)
				exit(1)

			if CONTROLLER_READY_MSG in out:
				break
		
		# Wait for Tofino to reeeally be ready
		time.sleep(TOFINO_WAITING_PERIOD)
	
	def modify_sampling_rate(self, sampling_rate):
		sed_cmd = f'sed -E -i \'s/#define SAMPLING [0-9]+/#define SAMPLING {sampling_rate}/g\''
		target = f'{self.p4_path}/includes/constants.p4'
		self.exec(f'{sed_cmd} {target}')
	
	def stop(self):
		self.kill(CONTROLLER_EXE_NAME)
		self.exec(f'rm -f {CONTROLLER_LOG_FILE} || true', must_succeed=False)

	def get_report(self):
		return self.get_files(f'{self.controller_path}/{CONTROLLER_REPORT_FILE}')

class TG_kernel(Host):
	def __init__(self, hostname, verbose=True):
		super().__init__('TG', hostname, verbose)

		# next, bind to kernel drivers
		self.exec(f'sudo {BIND_KERNEL_SCRIPT}', silence=True, must_succeed=False)
	
	def run(self, pcap, iface, duration=10):
		self.exec(f'sudo tcpreplay -K -i {iface} --duration={duration} -l 0 {pcap}', silence=True)

class Engine(Host):
	def __init__(self, hostname, peregrine_path, verbose=True):
		super().__init__('engine', hostname, verbose)

		self.peregrine_path = peregrine_path
		self.engine_path = f'{peregrine_path}/engine'
		self.engine_exe_path = f'{self.engine_path}/build/{ENGINE_EXE_NAME}'

		if not self.has_directory(self.peregrine_path):
			self.err(f'Directory not found: {self.peregrine_path}')

		if not self.has_directory(self.engine_path):
			self.err(f'Directory not found: {self.engine_path}')

		# Stop any instances running before running our own
		self.stop()
	
		# next, bind to kernel drivers
		self.exec(f'sudo {BIND_KERNEL_SCRIPT}', silence=True, must_succeed=False)

	def start(self, listen_iface):
		# build first
		self.exec('./build.sh', path=self.engine_path, silence=True)

		# now launching engine
		self.exec(f'sudo {self.engine_exe_path} -i {listen_iface} > {ENGINE_LOG_FILE} 2>&1',
			path=self.engine_path, background=True)
		
		# and wait for it to be ready
		while 1:
			time.sleep(1)

			ret, out, err = self.exec(f'cat {ENGINE_LOG_FILE}', capture_output=True)

			if not self.is_program_running(self.engine_exe_path):
				self.log('ERROR: Engine not running.')
				self.log('Dumping of log file:')
				print(out)
				exit(1)

			if ENGINE_READY_MSG in out:
				break

	def stop(self):
		self.kill(ENGINE_EXE_NAME)
		self.exec(f'rm -f {ENGINE_LOG_FILE}', must_succeed=False)
	
	def get_report(self):
		return self.get_files(f'{self.engine_path}/{ENGINE_REPORT_FILE}')

class KitNet(Host):
	def __init__(self, hostname, peregrine_path, verbose=True):
		super().__init__('kitnet', hostname, verbose)

		self.peregrine_path = peregrine_path
		self.kitnet_path = f'{peregrine_path}/engine/models/kitnet'
		self.kitnet_exe_path = f'{self.kitnet_path}/kitnet.py'

		if not self.has_directory(self.peregrine_path):
			self.err(f'Directory not found: {self.peregrine_path}')

		if not self.has_directory(self.kitnet_path):
			self.err(f'Directory not found: {self.kitnet_path}')

		# Stop any instances running before running our own
		self.stop()
	
	def start(self, feature_map_file, ensemble_layer_file, output_layer_file, train_stats_file):
		python_env_setup = 'source ./env/bin/activate'
		kitnet = self.kitnet_exe_path
		args = [
			'--feature_map', feature_map_file,
			'--ensemble_layer', ensemble_layer_file,
			'--output_layer', output_layer_file,
			'--train_stats', train_stats_file,
		]

		cmd = f'{python_env_setup} && {kitnet} {" ".join(args)} > {KITNET_LOG_FILE} 2>&1'
		
		# now launching kitnet model plugin
		self.exec(cmd, path=self.kitnet_path, background=True)

		# and wait for it to be ready
		while 1:
			time.sleep(1)

			ret, out, err = self.exec(f'cat {KITNET_LOG_FILE}', capture_output=True)
			
			if not self.is_program_running(self.kitnet_exe_path):
				self.log('ERROR: KitNet not running.')
				self.log('Dumping of log file:')
				print(out)
				exit(1)

			if KITNET_READY_MSG in out:
				break
		
	def stop(self):
		self.kill(KITNET_EXE_NAME)

if __name__ == '__main__':
	tofino = Tofino('tofino', '/root/peregrine')
	engine = Engine('gsd+e291427x1300274', '/home/fcp/peregrine')
	kitnet = KitNet('gsd+e291427x1300274', '/home/fcp/peregrine')
	tg = TG_kernel('gsd+e291427x1300275')
