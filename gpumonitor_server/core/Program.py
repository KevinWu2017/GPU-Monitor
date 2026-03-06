class Program:
    def __init__(self, pid, command, username, use_memory, start_time, duration):
        self.pid = pid
        self.command = command
        self.username = username
        self.use_memory = use_memory
        self.start_time = start_time
        self.duration = duration

    def json(self):
        return self.__dict__
