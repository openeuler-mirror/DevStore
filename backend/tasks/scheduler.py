#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# oeDeploy is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2025-07-18
# ======================================================================================================================

import functools
import multiprocessing
import queue
import threading
from concurrent.futures import ThreadPoolExecutor

from rest_framework import status
from rest_framework.response import Response

from constants.configs.task_scheduler_config import MAX_CONCURRENCY
from tasks.models import Task
from utils.logger import init_log

logger = init_log('run.log')

__all__ = ['scheduler', 'check_scheduler_load']


def check_scheduler_load(func):
    """
    装饰器，检查调度器 Scheduler 的负载
    """
    current_thread_count = 0
    for subprocess in scheduler.subprocesses.values():
        current_thread_count += len(subprocess.threads)
    if current_thread_count > Scheduler.max_concurrency:
        return Response({
            'is_success': False,
            'message': 'The current server load is too high. Please try again later.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


class SubProcess(multiprocessing.Process):

    def __init__(self, name, set_daemon=True, queue=None, condition=None, thread_pool_size=None, **kwargs):
        super(SubProcess, self).__init__(**kwargs)
        self.name = name
        self.daemon = set_daemon
        self.queue = queue
        self.condition = condition
        self.thread_pool_size = thread_pool_size
        self.threads = []

    @staticmethod
    def _insert_task_info(task):
        Task.objects.create(
            name=task.name,
            type=task.type,
            status=task.status,
            msg=task.msg
        )

    def _update_thread_info(self, task_thread):
        """
        当线程执行结束后，回调该函数
        """
        task = Task.objects.get(name=task_thread.name)
        if task_thread.exception():
            exception = task_thread.exception()
            task.status = Task.Status.FAIL
            task.msg = exception
            logger.error(f"Thread ({task_thread.name}) fail, error: {exception}")
        else:
            result = task_thread.result()
            task.status = Task.Status.SUCCESS
            task.msg = result
            logger.info(f"Thread ({task_thread.name}) done, result: {result}")
        self.threads.remove(task_thread)
        task.save()

    def run(self):
        threading_pool = ThreadPoolExecutor(self.thread_pool_size)
        while True:
            with self.condition:
                if self.queue.empty():
                    self.condition.wait()
            task = self.queue.get()
            task_thread = threading_pool.submit(task.run)
            self.threads.append(task_thread)
            task_thread.name = task.name
            task.status = Task.Status.IN_PROCESS
            self._insert_task_info(task)
            task_thread.add_done_callback(self._update_thread_info)


class Scheduler:
    # 机器核数
    cpu_count = multiprocessing.cpu_count()
    # 最大任务并发数
    max_concurrency = MAX_CONCURRENCY
    # 调度器主队列
    main_queue = queue.Queue()
    # 调度器主队列条件锁
    main_queue_condition = threading.Condition()
    # 子进程字典
    subprocesses = {}

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._start()

    def _get_thread_pool_size(self):
        # 防止获取cpu数量异常导致除数不正确的情况
        if self.cpu_count <= 0:
            self.cpu_count = 1
        # 当cpu数量为1时，线程池大小为任务数
        if self.cpu_count == 1:
            thread_pool_size = self.max_concurrency
        # 当cpu数量大于任务数量时，要创建的进程数变为任务数，每个进程中线程池大小为1
        elif self.cpu_count > self.max_concurrency:
            self.cpu_count = self.max_concurrency
            thread_pool_size = 1
        # 每个进程的线程池大小为任务数/进程数，如果有余数，那么每个进程中线程池大小加一
        else:
            thread_pool_size = int(self.max_concurrency / self.cpu_count)
            if self.max_concurrency % self.cpu_count != 0:
                thread_pool_size += 1
        return thread_pool_size

    def _start(self):
        thread_pool_size = self._get_thread_pool_size()
        self._start_subprocesses(thread_pool_size)
        distribute_task_thread = threading.Thread(target=self._distribute_task_to_subprocess)
        distribute_task_thread.daemon = True
        distribute_task_thread.start()

    def _start_subprocesses(self, thread_pool_size):
        for i in range(self.cpu_count):
            subprocess_queue = multiprocessing.Queue()
            subprocess_queue_condition = multiprocessing.Condition()
            subprocess = SubProcess(
                f"Process-{i}",
                queue=subprocess_queue,
                condition=subprocess_queue_condition,
                thread_pool_size=thread_pool_size
            )
            subprocess.start()
            self.subprocesses[subprocess.pid] = subprocess

    def _distribute_task_to_subprocess(self):
        subprocess_idx = 0
        subprocess_pids = list(self.subprocesses)
        while True:
            with self.main_queue_condition:
                if self.main_queue.empty():
                    self.main_queue_condition.wait()
            task = self.main_queue.get()
            subprocess_idx = 0 if subprocess_idx == self.cpu_count - 1 else subprocess_idx + 1
            subprocess = self.subprocesses.get(subprocess_pids[subprocess_idx])
            with subprocess.condition:
                subprocess.queue.put(task)
                subprocess.condition.notify()

    def add_task(self, task):
        with self.main_queue_condition:
            self.main_queue.put(task)
            self.main_queue_condition.notify()


scheduler = Scheduler()
