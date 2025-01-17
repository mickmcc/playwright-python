# Copyright (c) Microsoft Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, List, Pattern, Union
from urllib.parse import urljoin

from playwright._impl._api_structures import ExpectedTextValue, FrameExpectOptions
from playwright._impl._fetch import APIResponse
from playwright._impl._locator import Locator
from playwright._impl._page import Page
from playwright._impl._str_utils import escape_regex_flags


class AssertionsBase:
    def __init__(self, locator: Locator, is_not: bool = False) -> None:
        self._actual_locator = locator
        self._loop = locator._loop
        self._dispatcher_fiber = locator._dispatcher_fiber
        self._is_not = is_not

    async def _expect_impl(
        self,
        expression: str,
        expect_options: FrameExpectOptions,
        expected: Any,
        message: str,
    ) -> None:
        __tracebackhide__ = True
        expect_options["isNot"] = self._is_not
        if expect_options.get("timeout") is None:
            expect_options["timeout"] = 5_000
        if expect_options["isNot"]:
            message = message.replace("expected to", "expected not to")
        if "useInnerText" in expect_options and expect_options["useInnerText"] is None:
            del expect_options["useInnerText"]
        result = await self._actual_locator._expect(expression, expect_options)
        if result["matches"] == self._is_not:
            log = "\n".join(result.get("log", "")).strip()
            if log:
                log = "\nCall log:\n" + log
            if expected is not None:
                raise AssertionError(f"{message} '{expected}' {log}")
            raise AssertionError(f"{message} {log}")


class PageAssertions(AssertionsBase):
    def __init__(self, page: Page, is_not: bool = False) -> None:
        super().__init__(page.locator(":root"), is_not)
        self._actual_page = page

    @property
    def _not(self) -> "PageAssertions":
        return PageAssertions(self._actual_page, not self._is_not)

    async def to_have_title(
        self, title_or_reg_exp: Union[Pattern, str], timeout: float = None
    ) -> None:
        expected_values = to_expected_text_values(
            [title_or_reg_exp], normalize_white_space=True
        )
        __tracebackhide__ = True
        await self._expect_impl(
            "to.have.title",
            FrameExpectOptions(expectedText=expected_values, timeout=timeout),
            title_or_reg_exp,
            "Page title expected to be",
        )

    async def not_to_have_title(
        self, title_or_reg_exp: Union[Pattern, str], timeout: float = None
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_title(title_or_reg_exp, timeout)

    async def to_have_url(
        self, url_or_reg_exp: Union[str, Pattern], timeout: float = None
    ) -> None:
        __tracebackhide__ = True
        base_url = self._actual_page.context._options.get("baseURL")
        if isinstance(url_or_reg_exp, str) and base_url:
            url_or_reg_exp = urljoin(base_url, url_or_reg_exp)
        expected_text = to_expected_text_values([url_or_reg_exp])
        await self._expect_impl(
            "to.have.url",
            FrameExpectOptions(expectedText=expected_text, timeout=timeout),
            url_or_reg_exp,
            "Page URL expected to be",
        )

    async def not_to_have_url(
        self, url_or_reg_exp: Union[Pattern, str], timeout: float = None
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_url(url_or_reg_exp, timeout)


class LocatorAssertions(AssertionsBase):
    def __init__(self, locator: Locator, is_not: bool = False) -> None:
        super().__init__(locator, is_not)
        self._actual_locator = locator

    @property
    def _not(self) -> "LocatorAssertions":
        return LocatorAssertions(self._actual_locator, not self._is_not)

    async def to_contain_text(
        self,
        expected: Union[List[Union[Pattern, str]], Pattern, str],
        use_inner_text: bool = None,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        if isinstance(expected, list):
            expected_text = to_expected_text_values(
                expected, match_substring=True, normalize_white_space=True
            )
            await self._expect_impl(
                "to.contain.text.array",
                FrameExpectOptions(
                    expectedText=expected_text,
                    useInnerText=use_inner_text,
                    timeout=timeout,
                ),
                expected,
                "Locator expected to contain text",
            )
        else:
            expected_text = to_expected_text_values(
                [expected], match_substring=True, normalize_white_space=True
            )
            await self._expect_impl(
                "to.have.text",
                FrameExpectOptions(
                    expectedText=expected_text,
                    useInnerText=use_inner_text,
                    timeout=timeout,
                ),
                expected,
                "Locator expected to contain text",
            )

    async def not_to_contain_text(
        self,
        expected: Union[List[Union[Pattern, str]], Pattern, str],
        use_inner_text: bool = None,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_contain_text(expected, use_inner_text, timeout)

    async def to_have_attribute(
        self,
        name: str,
        value: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        expected_text = to_expected_text_values([value])
        await self._expect_impl(
            "to.have.attribute",
            FrameExpectOptions(
                expressionArg=name, expectedText=expected_text, timeout=timeout
            ),
            value,
            "Locator expected to have attribute",
        )

    async def not_to_have_attribute(
        self,
        name: str,
        value: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_attribute(name, value, timeout)

    async def to_have_class(
        self,
        expected: Union[List[Union[Pattern, str]], Pattern, str],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        if isinstance(expected, list):
            expected_text = to_expected_text_values(expected)
            await self._expect_impl(
                "to.have.class.array",
                FrameExpectOptions(expectedText=expected_text, timeout=timeout),
                expected,
                "Locator expected to have class",
            )
        else:
            expected_text = to_expected_text_values([expected])
            await self._expect_impl(
                "to.have.class",
                FrameExpectOptions(expectedText=expected_text, timeout=timeout),
                expected,
                "Locator expected to have class",
            )

    async def not_to_have_class(
        self,
        expected: Union[List[Union[Pattern, str]], Pattern, str],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_class(expected, timeout)

    async def to_have_count(
        self,
        count: int,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.have.count",
            FrameExpectOptions(expectedNumber=count, timeout=timeout),
            count,
            "Locator expected to have count",
        )

    async def not_to_have_count(
        self,
        count: int,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_count(count, timeout)

    async def to_have_css(
        self,
        name: str,
        value: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        expected_text = to_expected_text_values([value])
        await self._expect_impl(
            "to.have.css",
            FrameExpectOptions(
                expressionArg=name, expectedText=expected_text, timeout=timeout
            ),
            value,
            "Locator expected to have CSS",
        )

    async def not_to_have_css(
        self,
        name: str,
        value: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_css(name, value, timeout)

    async def to_have_id(
        self,
        id: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        expected_text = to_expected_text_values([id])
        await self._expect_impl(
            "to.have.id",
            FrameExpectOptions(expectedText=expected_text, timeout=timeout),
            id,
            "Locator expected to have ID",
        )

    async def not_to_have_id(
        self,
        id: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_id(id, timeout)

    async def to_have_js_property(
        self,
        name: str,
        value: Any,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.have.property",
            FrameExpectOptions(
                expressionArg=name, expectedValue=value, timeout=timeout
            ),
            value,
            "Locator expected to have JS Property",
        )

    async def not_to_have_js_property(
        self,
        name: str,
        value: Any,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_js_property(name, value, timeout)

    async def to_have_value(
        self,
        value: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        expected_text = to_expected_text_values([value])
        await self._expect_impl(
            "to.have.value",
            FrameExpectOptions(expectedText=expected_text, timeout=timeout),
            value,
            "Locator expected to have Value",
        )

    async def not_to_have_value(
        self,
        value: Union[str, Pattern],
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_value(value, timeout)

    async def to_have_text(
        self,
        expected: Union[List[Union[Pattern, str]], Pattern, str],
        use_inner_text: bool = None,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        if isinstance(expected, list):
            expected_text = to_expected_text_values(
                expected, normalize_white_space=True
            )
            await self._expect_impl(
                "to.have.text.array",
                FrameExpectOptions(
                    expectedText=expected_text,
                    useInnerText=use_inner_text,
                    timeout=timeout,
                ),
                expected,
                "Locator expected to have text",
            )
        else:
            expected_text = to_expected_text_values(
                [expected], normalize_white_space=True
            )
            await self._expect_impl(
                "to.have.text",
                FrameExpectOptions(
                    expectedText=expected_text,
                    useInnerText=use_inner_text,
                    timeout=timeout,
                ),
                expected,
                "Locator expected to have text",
            )

    async def not_to_have_text(
        self,
        expected: Union[List[Union[Pattern, str]], Pattern, str],
        use_inner_text: bool = None,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_have_text(expected, use_inner_text, timeout)

    async def to_be_checked(
        self,
        timeout: float = None,
        checked: bool = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.checked"
            if checked is None or checked is True
            else "to.be.unchecked",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be checked",
        )

    async def not_to_be_checked(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_checked(timeout)

    async def to_be_disabled(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.disabled",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be disabled",
        )

    async def not_to_be_disabled(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_disabled(timeout)

    async def to_be_editable(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.editable",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be editable",
        )

    async def not_to_be_editable(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_editable(timeout)

    async def to_be_empty(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.empty",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be empty",
        )

    async def not_to_be_empty(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_empty(timeout)

    async def to_be_enabled(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.enabled",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be enabled",
        )

    async def not_to_be_enabled(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_enabled(timeout)

    async def to_be_hidden(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.hidden",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be hidden",
        )

    async def not_to_be_hidden(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_hidden(timeout)

    async def to_be_visible(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.visible",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be visible",
        )

    async def not_to_be_visible(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_visible(timeout)

    async def to_be_focused(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._expect_impl(
            "to.be.focused",
            FrameExpectOptions(timeout=timeout),
            None,
            "Locator expected to be focused",
        )

    async def not_to_be_focused(
        self,
        timeout: float = None,
    ) -> None:
        __tracebackhide__ = True
        await self._not.to_be_focused(timeout)


class APIResponseAssertions:
    def __init__(self, response: APIResponse, is_not: bool = False) -> None:
        self._loop = response._loop
        self._dispatcher_fiber = response._dispatcher_fiber
        self._is_not = is_not
        self._actual = response

    @property
    def _not(self) -> "APIResponseAssertions":
        return APIResponseAssertions(self._actual, not self._is_not)

    async def to_be_ok(
        self,
    ) -> None:
        __tracebackhide__ = True
        if self._is_not is not self._actual.ok:
            return
        message = f"Response status expected to be within [200..299] range, was '{self._actual.status}'"
        if self._is_not:
            message = message.replace("expected to", "expected not to")
        log_list = await self._actual._fetch_log()
        log = "\n".join(log_list).strip()
        if log:
            message += f"\n Call log:\n{log}"
        raise AssertionError(message)

    async def not_to_be_ok(self) -> None:
        __tracebackhide__ = True
        await self._not.to_be_ok()


def expected_regex(
    pattern: Pattern, match_substring: bool, normalize_white_space: bool
) -> ExpectedTextValue:
    expected = ExpectedTextValue(
        regexSource=pattern.pattern,
        regexFlags=escape_regex_flags(pattern),
        matchSubstring=match_substring,
        normalizeWhiteSpace=normalize_white_space,
    )
    return expected


def to_expected_text_values(
    items: Union[List[Pattern], List[str], List[Union[str, Pattern]]],
    match_substring: bool = False,
    normalize_white_space: bool = False,
) -> List[ExpectedTextValue]:
    out: List[ExpectedTextValue] = []
    assert isinstance(items, list)
    for item in items:
        if isinstance(item, str):
            out.append(
                ExpectedTextValue(
                    string=item,
                    matchSubstring=match_substring,
                    normalizeWhiteSpace=normalize_white_space,
                )
            )
        elif isinstance(item, Pattern):
            out.append(expected_regex(item, match_substring, normalize_white_space))
    return out
