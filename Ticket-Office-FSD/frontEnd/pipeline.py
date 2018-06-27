from subprocess import Popen, PIPE, STDOUT


class PipeLine(object):

    def __init__(self, exec_path):
        self.proc = Popen([exec_path], stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def write(self, cmd):
        self.proc.stdin.write((cmd + '\n').encode())
        self.proc.stdin.flush()

    def readline(self):
        return self.proc.stdout.readline().decode().strip('\n')


if __name__ == "__main__":
    pip = PipeLine('./train_modified')
    pip.write('register qian \0 831800 qina@sjtu.edu.cn 13328179990')
    print(pip.readline())
    pip.write('query_profile qian')
    reply = pip.readline()
    print(reply.split(' ')[1])
    pip.write('clean')
    pip.write('exit')

