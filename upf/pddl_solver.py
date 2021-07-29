# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This module defines an interface for a generic PDDL planner."""

import tempfile
import os
import re
import shutil
import upf
import subprocess
from upf.shortcuts import *
from upf.io.pddl_writer import PDDLWriter
from upf.exceptions import UPFException
from typing import Optional


class PDDLSolver(upf.Solver):
    """
    This class is the interface of a generic PDDL solver
    that can be invocated through a subprocess call.
    """

    def __init__(self, needs_requirements=True):
        upf.Solver.__init__(self)
        self._needs_requirements = needs_requirements

    @staticmethod
    def is_oneshot_planner() -> bool:
        return True

    def _get_cmd(self, domanin_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        raise NotImplementedError

    def _plan_from_file(self, problem: 'upf.Problem', plan_filename: str) -> 'upf.Plan':
        actions = []
        with open(plan_filename) as plan:
            for line in plan.readlines():
                if re.match(r'^\s*(;.*)?$', line):
                    continue
                res = re.match(r'^\s*\(\s*([\w?-]+)((\s+[\w?-]+)*)\s*\)\s*$', line)
                if res:
                    action = problem.action(res.group(1))
                    parameters = []
                    for p in res.group(2).split():
                        parameters.append(ObjectExp(problem.object(p)))
                    actions.append(upf.ActionInstance(action, tuple(parameters)))
                else:
                    raise UPFException('Error parsing plan generated by ' + self.__class__.__name__)
        return upf.SequentialPlan(actions)

    def solve(self, problem: 'upf.Problem') -> Optional['upf.Plan']:
        w = PDDLWriter(problem, self._needs_requirements)
        plan = None
        with tempfile.TemporaryDirectory() as tempdir:
            domanin_filename = os.path.join(tempdir, 'domain.pddl')
            problem_filename = os.path.join(tempdir, 'problem.pddl')
            plan_filename = os.path.join(tempdir, 'plan.txt')
            w.write_domain(domanin_filename)
            w.write_problem(problem_filename)

            cmd = self._get_cmd(domanin_filename, problem_filename, plan_filename)
            res = subprocess.run(cmd, capture_output=True)

            if not os.path.isfile(plan_filename):
                print(res.stderr.decode())
            else:
                plan = self._plan_from_file(problem, plan_filename)

        return plan

    def destroy(self):
        pass
