#!/usr/bin/env python3

import subprocess
import time
import os

SCRIPT_DIR             = os.path.dirname(os.path.realpath(__file__))

TOFINO_HOSTNAME        = 'tofino'
TG_HOSTNAME            = 'gsd+e291427x1300275'
ENGINE_HOSTNAME        = 'gsd+e291427x1300274'
KITNET_HOSTNAME        = 'gsd+e291427x1300274'

TOFINO_PEREGRINE_PATH  = '/root/peregrine'
ENGINE_PEREGRINE_PATH  = '/home/fcp/peregrine'

P4_PATH                = f'{TOFINO_PEREGRINE_PATH}/p4'
CONTROLLER_PATH        = f'{TOFINO_PEREGRINE_PATH}/controller'
ENGINE_PATH            = f'{ENGINE_PEREGRINE_PATH}/engine'
KITNET_PATH            = f'{ENGINE_PATH}/models/kitnet'

CONTROLLER_EXE_NAME    = 'peregrine-controller'
ENGINE_EXE_NAME        = 'engine'
KITNET_EXE_NAME        = 'python' # oof

CONTROLLER_EXE_PATH    = f'{CONTROLLER_PATH}/build/{CONTROLLER_EXE_NAME}'
ENGINE_EXE_PATH        = f'{ENGINE_PATH}/build/{ENGINE_EXE_NAME}'
KITNET_EXE_PATH        = f'{KITNET_PATH}/kitnet.py'

CONTROLLER_LOG_FILE    = '/tmp/run-with-hw.log'
CONTROLLER_READY_MSG   = 'Peregrine controller is ready.'
CONTROLLER_REPORT_FILE = 'peregrine-controller.tsv'

ENGINE_LOG_FILE        = '/tmp/engine.log'
ENGINE_READY_MSG       = 'Listening interface'
ENGINE_REPORT_FILE     = 'peregrine-engine.tsv'
ENGINE_LISTEN_IFACE    = 'enp216s0f1'

KITNET_LOG_FILE        = '/tmp/kitnet.log'
KITNET_READY_MSG       = 'Listening on'

BIND_KERNEL_SCRIPT     = '/home/fcp/bind-e810-kernel.sh'
BIND_DPDK_SCRIPT       = '/home/fcp/bind-igb_uio.sh'

class Host:
	def __init__(self, name, hostname):
		self.name = name
		self.hostname = hostname
		self.test_connection()

	def exec(self, cmd, path=None, silence=False, background=False,
			must_succeed=True, capture_output=False, allocate_tty=False):
		assert(type(cmd) == str)

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
		
		if allocate_tty:
			ssh_flags.append('-t')
		
		cmd = [ 'ssh' ] + ssh_flags + [ self.hostname, remote_cmd ]

		if not capture_output:
			stdout = subprocess.DEVNULL if silence or background else None
			stderr = subprocess.DEVNULL if silence or background else None
			proc = subprocess.run(cmd, stdout=stdout, stderr=stderr)
		else:
			proc = subprocess.run(cmd, capture_output=True, text=True)

		if not background and must_succeed and proc.returncode != 0:
			self.log(f'Command failed.')
			self.log(f'  command:  \"{cmd}\"')
			self.log(f'  ret code: {proc.returncode}')
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
		
		if proc.returncode != 0:
			self.log(f'Command failed (ret={proc.returncode}).')
			exit(1)
	
	def kill(self, program_name, must_succeed=False):
		self.exec(f'sudo killall {program_name}', silence=True, must_succeed=must_succeed)
	
	def log(self, msg):
		print(f'[{self.name}] {msg}')

class Tofino(Host):
	def __init__(self):
		super().__init__('tofino', TOFINO_HOSTNAME)

		# Stop any instances running before running our own
		self.stop()
	
	def install(self):
		self.exec('make install', path=P4_PATH)
	
	def start(self, sampling_rate):		
		self.exec(f'./run-with-hw.sh {sampling_rate} > {CONTROLLER_LOG_FILE} 2>&1',
			path=CONTROLLER_PATH, background=True)
		
		while 1:
			ret, out, err = self.exec(f'cat {CONTROLLER_LOG_FILE}', capture_output=True)
			time.sleep(1)

			if CONTROLLER_READY_MSG in out:
				break
	
	def stop(self):
		self.kill(CONTROLLER_EXE_NAME)
		self.exec(f'rm -f {CONTROLLER_LOG_FILE}', must_succeed=False)

	def get_report(self):
		self.get_files(f'{CONTROLLER_PATH}/{CONTROLLER_REPORT_FILE}')

class TG(Host):
	def __init__(self):
		super().__init__('TG', TG_HOSTNAME)

class Engine(Host):
	def __init__(self):
		super().__init__('engine', ENGINE_HOSTNAME)
	
	def start(self, listen_iface):
		# build first
		self.exec('./build.sh', path=ENGINE_PATH, silence=True)

		# next, bind to kernel drivers
		self.exec(f'sudo {BIND_KERNEL_SCRIPT}', silence=True, must_succeed=False)

		# now launching engine
		self.exec(f'sudo {ENGINE_EXE_PATH} -i {listen_iface} > {ENGINE_LOG_FILE} 2>&1',
			path=ENGINE_PATH, background=True)
		
		# and wait for it to be ready
		while 1:
			ret, out, err = self.exec(f'cat {ENGINE_LOG_FILE}', capture_output=True)
			time.sleep(1)

			if ENGINE_READY_MSG in out:
				break

	def stop(self):
		self.kill(ENGINE_EXE_NAME)
		self.exec(f'rm -f {ENGINE_LOG_FILE}', must_succeed=False)
	
	def get_report(self):
		self.get_files(f'{ENGINE_PATH}/{ENGINE_REPORT_FILE}')

class KitNet(Host):
	def __init__(self):
		super().__init__('kitnet', KITNET_HOSTNAME)
	
	def start(self, feature_map, ensemble_layer, output_layer, train_stats):
		python_env_setup = 'source ./env/bin/activate'
		kitnet = KITNET_EXE_PATH
		args = [
			'--feature_map', feature_map,
			'--ensemble_layer', ensemble_layer,
			'--output_layer', output_layer,
			'--train_stats', train_stats
		]

		# cmd = f'{python_env_setup} && {kitnet} {" ".join(args)} & > {KITNET_LOG_FILE} 2>&1'
		cmd = f'{python_env_setup} && {kitnet} {" ".join(args)} > {KITNET_LOG_FILE} 2>&1'
		
		# now launching kitnet model plugin
		# self.exec(cmd, path=KITNET_PATH, background=True, allocate_tty=True)
		self.exec(cmd, path=KITNET_PATH, allocate_tty=True)

		# and wait for it to be ready
		while 1:
			ret, out, err = self.exec(f'cat {KITNET_LOG_FILE}', capture_output=True)
			time.sleep(1)

			if KITNET_READY_MSG in out:
				break

if __name__ == '__main__':
	tofino = Tofino()
	tg = TG()
	engine = Engine()
	kitnet = KitNet()

	# tofino.install()
	# tofino.start(16)
	# tofino.stop()
	# tofino.get_report()

	# engine.start(ENGINE_LISTEN_IFACE)
	# engine.stop()
	# engine.get_report()

	kitnet.start(
		'~/models/m-10/os-scan-m-10-fm.txt',
		'~/models/m-10/os-scan-m-10-el.txt',
		'~/models/m-10/os-scan-m-10-ol.txt',
		'~/models/m-10/os-scan-m-10-train-stats.txt',
	)


