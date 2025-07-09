from typing import List

from core.Program import Program


class GPU:

    def __init__(self, num, name, use_memory, total_memory, temp, fan, pwr, gpu_util, program_list):
        self.num = num
        self.name = name
        self.fan = fan
        self.temp = temp
        self.pwr = pwr
        self.use_memory = use_memory
        self.total_memory = total_memory
        self.gpu_util = gpu_util  # GPU利用率百分比
        self.program_list: List[Program] = program_list

    def json(self):
        return {
            'num': self.num,
            'name': self.name,
            'fan': self.fan,
            'temp': self.temp,
            'pwr': self.pwr,
            'use_memory': self.use_memory,
            'total_memory': self.total_memory,
            'gpu_util': self.gpu_util,  # GPU利用率
            'program_list': [program.json() for program in self.program_list]
        }