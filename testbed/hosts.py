#!/usr/bin/env python3

import subprocess
import time
import os

SCRIPT_DIR             = os.path.dirname(os.path.realpath(__file__))

TOFINO_HOSTNAME        = 'tofino'
TG_HOSTNAME            = 'gsd+e291427x1300275'
ENGINE_HOSTNAME        = 'gsd+e291427x1300274'
KITNET_HOSTNAME        = 'gsd+e291427x1300274'

PEREGRINE_PATH         = '/root/peregrine'
P4_PATH                = f'{PEREGRINE_PATH}/p4'
CONTROLLER_PATH        = f'{PEREGRINE_PATH}/controller'
ENGINE_PATH            = f'{PEREGRINE_PATH}/engine'

CONTROLLER_EXE_NAME   = 'peregrine-controller'
ENGINE_EXE_NAME       = 'engine'
CONTROLLER_EXE_PATH   = f'{CONTROLLER_PATH}/build/{CONTROLLER_EXE_NAME}'
ENGINE_EXE_PATH       = f'{PEREGRINE_PATH}/build/{ENGINE_EXE_NAME}'

CONTROLLER_LOG_FILE    = '/tmp/run-with-hw.log'
CONTROLLER_READY_MSG   = 'Peregrine controller is ready.'
CONTROLLER_REPORT_FILE = 'peregrine-controller.tsv'

class Host:
	def __init__(self, name, hostname):
		self.name = name
		self.hostname = hostname
		self.test_connection()

	def exec(self, cmd, path=None, silence=False, background=False, must_succeed=True, capture_output=False):
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

		ssh_flags = [ '-o', 'PasswordAuthentication=no' ]

		if background:
			ssh_flags.append('-f')
		
		cmd = [ 'ssh' ] + ssh_flags + [ self.hostname, remote_cmd ]

		if not capture_output:
			stdout = subprocess.DEVNULL if silence or background else None
			stderr = subprocess.DEVNULL if silence or background else None
			proc = subprocess.run(cmd, stdout=stdout, stderr=stderr)
		else:
			proc = subprocess.run(cmd, capture_output=True, text=True)

		if not background and must_succeed and proc.returncode != 0:
			self.log(f'Command failed (ret={proc.returncode}).')
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
	
	def start(self):		
		self.exec(f'./run-with-hw.sh > {CONTROLLER_LOG_FILE} 2>&1',
			path=CONTROLLER_PATH, background=True)
		
		while 1:
			ret, out, err = self.exec(f'cat {CONTROLLER_LOG_FILE}',
				path=CONTROLLER_PATH, capture_output=True)
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

class KitNet(Host):
	def __init__(self):
		super().__init__('kitnet', KITNET_HOSTNAME)

if __name__ == '__main__':
	tofino = Tofino()
	tg = TG()
	engine = Engine()
	kitnet = KitNet()

	# tofino.install()
	# tofino.start()
	# tofino.stop()
	tofino.get_report()