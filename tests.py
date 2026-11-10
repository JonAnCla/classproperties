"""Full test suite for 'typed_classproperties' library."""

__all__: "Sequence[str]" = ("TestCachedClassProperty", "TestClassProperty")
__lazy_modules__: "Sequence[str]" = ("pytest",)

import abc
import sys
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

import pytest

from typed_classproperties import cached_classproperty, classproperty, protect_classproperties

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import ClassVar

    if sys.version_info >= (3, 12):
        from typing import Self
    else:
        from typing_extensions import Self


T_class = TypeVar("T_class", covariant=True)  # noqa: PLC0105
T_func = TypeVar("T_func")


class Holder(Protocol[T_class]):  # ty: ignore[invalid-protocol]
    cached_prop_exec_count: "ClassVar[int]"

    @classproperty
    def HELD_VALUE(cls: type["Self"]) -> T_class:  # noqa: N802
        ...

    @cached_classproperty
    def CACHED_HELD_VALUE(cls: type["Self"]) -> T_class:  # noqa: N802
        ...


class BaseTestClassProperty(abc.ABC):  # noqa: B024
    """Abstract base class for all test classes."""

    @classmethod
    def _get_cls_definition(cls, test_value: T_func) -> type[Holder[T_func]]:
        @protect_classproperties
        class _HolderClass(Holder[object]):  # noqa: CAR160
            cached_prop_exec_count = 0

            @classproperty
            @override
            def HELD_VALUE(cls: type["Self"]) -> T_func:
                return test_value

            @cached_classproperty
            @override
            def CACHED_HELD_VALUE(cls: type["Self"]) -> T_func:
                cls.cached_prop_exec_count += 1
                return test_value

        return cast("type[Holder[T_func]]", _HolderClass)


class TestClassProperty(BaseTestClassProperty):
    """Test the `classproperty` decorator."""

    def test_classproperty_class(self) -> None:
        """Test that a classproperty correctly returns its value from a class."""
        assert self._get_cls_definition(1000).HELD_VALUE == 1000  # ty: ignore[unresolved-attribute]

    def test_classproperty_instance(self) -> None:
        """Test that a classproperty correctly returns its value from an instance."""
        assert self._get_cls_definition(2000)().HELD_VALUE == 2000

    def test_typed_subclasses(self) -> None:
        """Test that subclasses can override classproperties."""

        class _BaseClass(abc.ABC):  # noqa: CAR160
            @classproperty
            @abc.abstractmethod
            def MY_PROPERTY(cls) -> str:  # noqa: N802
                pass

        class _SubClass(_BaseClass):  # noqa: CAR160
            @classproperty
            @override
            def MY_PROPERTY(cls) -> str:
                return ""

    def test_classproperty_not_writeable_on_class(self) -> None:
        """Test that a classproperty cannot be overwritten on a class."""
        holder_class: type[Holder[int]] = self._get_cls_definition(3000)

        with pytest.raises(AttributeError, match=r"\Aclassproperty '.+ has no setter\Z"):
            holder_class.HELD_VALUE = 4000  # type: ignore[ty:invalid-assignment]

    def test_classproperty_not_writeable_on_instance(self) -> None:
        """Test that a classproperty cannot be overwritten on a class."""
        holder_instance: Holder[int] = self._get_cls_definition(3000)()

        with pytest.raises(AttributeError, match=r"\Aclassproperty '.+ has no setter\Z"):
            holder_instance.HELD_VALUE = 4000


class TestCachedClassProperty(BaseTestClassProperty):
    """Test the `cached_classproperty` decorator."""

    def test_cached_classproperty_class(self) -> None:
        """Test that a `cached_classproperty` correctly returns its value from a class."""
        created_class: type[Holder[int]] = self._get_cls_definition(3000)
        assert created_class.cached_prop_exec_count == 0
        assert created_class.CACHED_HELD_VALUE == 3000  # ty: ignore[unresolved-attribute]
        assert created_class.cached_prop_exec_count == 1

    def test_cached_classproperty_executed_once(self) -> None:
        """Test that a `cached_classproperty` correctly returns the cached value."""
        created_class: type[Holder[int]] = self._get_cls_definition(4000)
        assert created_class.cached_prop_exec_count == 0
        assert created_class.CACHED_HELD_VALUE == 4000  # ty: ignore[unresolved-attribute]
        assert created_class.cached_prop_exec_count == 1
        assert created_class.CACHED_HELD_VALUE == 4000
        assert created_class.cached_prop_exec_count == 1

    def test_cached_classproperty_delete_cache(self) -> None:
        """Test that removing a `cached_classproperty`'s cached value functions correctly."""
        created_class: type[Holder[int]] = self._get_cls_definition(5000)
        assert created_class.cached_prop_exec_count == 0
        assert created_class.CACHED_HELD_VALUE == 5000  # ty: ignore[unresolved-attribute]
        assert created_class.cached_prop_exec_count == 1
        cached_classproperty.remove_cached_value(created_class, "CACHED_HELD_VALUE")
        assert created_class.CACHED_HELD_VALUE == 5000
        assert created_class.cached_prop_exec_count == 2

    def test_cached_classproperty_instance(self) -> None:
        """Test that a `cached_classproperty` returns the correct value from an instance."""
        created_instance: Holder[int] = self._get_cls_definition(6000)()
        assert created_instance.cached_prop_exec_count == 0
        assert created_instance.CACHED_HELD_VALUE == 6000
        assert created_instance.cached_prop_exec_count == 1

    def test_cached_classproperty_executed_once_instance(self) -> None:
        """Test that a `cached_classproperty` returns its value from an instance only once."""
        created_instance: Holder[int] = self._get_cls_definition(8000)()
        assert created_instance.cached_prop_exec_count == 0
        assert created_instance.CACHED_HELD_VALUE == 8000
        assert created_instance.cached_prop_exec_count == 1
        assert created_instance.CACHED_HELD_VALUE == 8000
        assert created_instance.cached_prop_exec_count == 1

    def test_cached_classproperty_executed_once_instance_cls_share_same_cached_val(
        self,
    ) -> None:
        """Test that a `cached_classproperty` returns its value from a shared class once."""
        created_class: type[Holder[int]] = self._get_cls_definition(9000)
        created_instance: Holder[int] = created_class()
        assert created_instance.cached_prop_exec_count == 0
        assert created_instance.CACHED_HELD_VALUE == 9000
        assert created_instance.cached_prop_exec_count == 1
        assert created_instance.CACHED_HELD_VALUE == 9000
        assert created_instance.cached_prop_exec_count == 1

        assert created_class.cached_prop_exec_count == 1
        assert created_class.CACHED_HELD_VALUE == 9000
        assert created_class.cached_prop_exec_count == 1

        created_instance = created_class()
        assert created_instance.cached_prop_exec_count == 1
        assert created_instance.CACHED_HELD_VALUE == 9000
        assert created_instance.cached_prop_exec_count == 1

    def test_cached_classproperty_not_writeable_on_class(self) -> None:
        """Test that a cached_classproperty cannot be overwritten on a class."""
        holder_class: type[Holder[int]] = self._get_cls_definition(3000)

        with pytest.raises(
            AttributeError, match=r"\Acached_classproperty '.+ has no setter\Z"
        ):
            holder_class.CACHED_HELD_VALUE = 4000  # type: ignore[ty:invalid-assignment]

    def test_classproperty_not_writeable_on_instance(self) -> None:
        """Test that a classproperty cannot be overwritten on a class."""
        holder_instance: Holder[int] = self._get_cls_definition(3000)()

        with pytest.raises(
            AttributeError, match=r"\Acached_classproperty '.+ has no setter\Z"
        ):
            holder_instance.CACHED_HELD_VALUE = 4000  # ty: ignore[invalid-assignment]
