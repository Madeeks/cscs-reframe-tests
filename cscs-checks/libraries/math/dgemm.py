import reframe as rfm
import reframe.utility.sanity as sn


@rfm.required_version('>=2.14')
@rfm.simple_test
class DGEMMTest(rfm.RegressionTest):
    def __init__(self):
        super().__init__()
        self.descr = 'DGEMM performance test'
        self.sourcepath = 'dgemm.c'

        self.sanity_patterns = self.eval_sanity()
        # the perf patterns are automaticaly generated inside sanity
        self.perf_patterns = {}

        self.valid_systems = ['daint:gpu', 'daint:mc', 'dom:gpu', 'dom:mc']
        self.valid_prog_environs = ['PrgEnv-gnu']

        self.num_tasks = 0
        self.num_tasks_per_node = 1
        self.num_tasks_per_core = 1
        self.num_tasks_per_socket = 1
        self.use_multithreading = False

        self.build_system = 'SingleSource'
        self.build_system.cflags = ['-O3']

        self.sys_reference = {
            'daint:gpu': (460, -0.1, None),
            'daint:mc': (460, -0.1, None),
            'dom:gpu': (460, -0.1, None),
            'dom:mc': (460, -0.1, None),
            'monch:compute': (350, -0.1, None),
        }

        self.maintainers = ['AJ', 'VH', 'VK']
        self.tags = {'production'}


    def setup(self, partition, environ, **job_opts):
        if partition.fullname in ['daint:gpu', 'dom:gpu']:
            self.num_cpus_per_task = 12
            self.executable_opts = ['6144', '12288', '3072']
        elif partition.fullname in ['daint:mc', 'dom:mc']:
            self.num_cpus_per_task = 36
            self.executable_opts = ['6144', '12288', '3072']
        elif partition.fullname in ['monch:compute']:
            self.num_cpus_per_task = 20
            self.executable_opts = ['5000', '5000', '5000']
            self.build_system.cflags += ['-I$EBROOTOPENBLAS/include']
            self.build_system.ldflags = ['-L$EBROOTOPENBLAS/lib', '-lopenblas',
                                         '-lpthread', '-lgfortran']

        self.variables = {
            'OMP_NUM_THREADS': str(self.num_cpus_per_task),
        }
        super().setup(partition, environ, **job_opts)


    @sn.sanity_function
    def eval_sanity(self):
        failure_msg = ""

        all_tested_nodes = sn.evaluate(sn.extractall(
            r'(?P<name>.*):\s+Time for \d+ DGEMM operations',
            self.stdout
        ))
        num_tested_nodes = len(all_tested_nodes)

        # if num_tested_nodes != self.job.num_tasks:
        if num_tested_nodes != self.job.num_tasks:
            failure_msg = ('Requested %s nodes, but found %s nodes' %
                            (self.job.num_tasks, num_tested_nodes))
            sn.assert_false(failure_msg, msg=failure_msg)

        for node in all_tested_nodes:
            nodename  = node.group('name')

            if self.sys_reference[self.current_partition.fullname]:
                partition_name = self.current_partition.fullname
                ref_name = '%s:%s' % (partition_name, nodename)
                self.reference[ref_name] = self.sys_reference[partition_name]
                self.perf_patterns[nodename] = sn.extractsingle(
                    r'%s:\s+Flops based on.*:\s+(?P<gflops>.*)\sGFlops\/sec' %
                    nodename, self.stdout, 'gflops', float)

        return sn.assert_false(failure_msg, msg=failure_msg)
