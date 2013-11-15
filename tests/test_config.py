import nose
from nose.tools import raises
import utils

import rez.rez_config
from rez.rez_config import Resolver
from rez.rez_exceptions import PkgsUnresolvedError, PkgConfigNotResolvedError, PkgConflictError, PkgNotFoundError
from rez.public_enums import RESOLVE_MODE_LATEST, RESOLVE_MODE_EARLIEST
from rez.rez_filesys import _g_os_pkg as OS_PKG

def check_basic_resolve(pkgs, assertions,
                        resolver_args=dict(resolve_mode=RESOLVE_MODE_LATEST),
                        resolve_args={}):
    resolver = rez.rez_config.Resolver(**resolver_args)
    result = resolver.resolve(pkgs, **resolve_args)
    assert_resolve_result(result, assertions)

def assert_resolve_result(result, assertions):
    assert result is not None
    pkg_ress, commands, dot_graph, num_fails = result

    res = [p.short_name() for p in pkg_ress]
    assert res == assertions, res

class TestResolve(utils.RezTest):
    def setUp(self):
        self.cleanup()
        self.make_release_package('Linux')
        # real world examples are so much easier to follow
        self.make_local_package('python', '2.7.4')
        self.make_release_package('python', '2.6.4')
        self.make_release_package('python', '2.6.1')
        self.make_release_package('maya', '2012', requires=['python-2.6'])
        self.make_release_package('maya', '2013', requires=['python-2.6'])
        self.make_release_package('maya', '2014', requires=['python-2.7'])
        self.make_release_package('nuke', '7.1.2', requires=['python-2.6'])
        self.make_release_package('arnold', '4.0.16.0', requires=['python'])
        self.make_release_package('mtoa', '0.25.0',
                                  requires=['arnold-4.0.16'],
                                  variants=[['maya-2014'], ['maya-2013']]
                                  )

    def test_latest(self):
        for ins, outs in [
                          (['python'],
                           ['python-2.7.4', OS_PKG]),
                          (['python-2.6'],
                           ['python-2.6.4', OS_PKG]),
                          (['maya'],
                           ['python-2.7.4', 'maya-2014', OS_PKG]),
                          (['maya', 'python-2.6'],
                           ['python-2.6.4', 'maya-2013', OS_PKG]),
                          (['maya', 'nuke-7'],
                           ['python-2.6.4', 'nuke-7.1.2', 'maya-2013', OS_PKG]),
                          (['nuke-7'],
                           ['python-2.6.4', 'nuke-7.1.2', OS_PKG]),
                          (['mtoa'],
                           ['python-2.7.4', 'maya-2014', 'arnold-4.0.16.0', 'mtoa-0.25.0', OS_PKG]),
                          ]:
            yield check_basic_resolve, ins, outs

    def test_earliest(self):
        for ins, outs in [(['python'],
                           ['python-2.6.1', OS_PKG]),
                          (['python-2.6'],
                           ['python-2.6.1', OS_PKG]),
                          (['maya'],
                           ['python-2.6.1', 'maya-2012', OS_PKG]),
                          (['maya', 'python-2.6'],
                           ['python-2.6.1', 'maya-2012', OS_PKG]),
                          (['maya', 'nuke'],
                           ['python-2.6.1', 'nuke-7.1.2', 'maya-2012', OS_PKG]),
                          ]:
            yield check_basic_resolve, ins, outs, dict(resolve_mode=RESOLVE_MODE_EARLIEST)

    def test_failures(self):
        for ins, exc in [(['python-2.7', 'python-2.6'], PkgConflictError), # straight conflict
                         (['nuke-6'], PkgNotFoundError), # does not exist
                         # I dont understand the practical difference between these:
                         (['maya-2014', 'nuke-7'], PkgConfigNotResolvedError),
                         (['maya-2014', 'nuke-7+'], PkgsUnresolvedError),
                         ]:
            # `raises` is a decorator that returns a modified test function that
            # passes the test if the exception is raised
            yield raises(exc)(check_basic_resolve), ins, None


if __name__ == '__main__':
    nose.main()