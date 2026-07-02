"""
欧冶 (ouyeel.com) 瑞数6 配方

从旧脚本 gen_cookie_iv8 搬过来的 DOM Mock + 环境配置
"""
from recipes.base import Recipe, recipe_matcher

OUYEEL_DOM_PATCH = r"""
// ===== 从旧脚本搬过来的精确补环境 =====
// 1. self = top = window
self = top = window;

// 2. 全局函数 Mock
window.setInterval = function() { return 0; };
window.setTimeout = function() { return 0; };
window.clearTimeout = function() {};
window.clearInterval = function() {};
window.addEventListener = function() {};
window.ActiveXObject = undefined;
window.attachEvent = function() {};

// 3. XMLHttpRequest
var XMLHttpRequest = function XMLHttpRequest() {};
XMLHttpRequest.prototype.open = function() {};
XMLHttpRequest.prototype.send = function() {};
XMLHttpRequest.prototype.setRequestHeader = function() {};
XMLHttpRequest.prototype.abort = function() {};
XMLHttpRequest.prototype.getResponseHeader = function() { return null; };

// 4. HTML 元素
window.HTMLFormElement = function() {};
window.HTMLAnchorElement = function() {};

var div = {
    getElementsByTagName: function(ele) {
        if (ele === 'i') return [];
        return [];
    }
};
var head = { removeChild: function(ele) {} };

var script = {
    getAttribute: function(ele) {
        if (ele === 'r') return META_R;
        return null;
    },
    parentElement: head
};

var meta = {
    getAttribute: function(ele) {
        if (ele === 'r') return META_R;
        return null;
    },
    parentNode: head,
    content: META_CONTENT
};

var form = {};
var input = {};

// 5. Document
document.createElement = function(ele) {
    if (ele === 'div') return div;
    if (ele === 'form') return form;
    if (ele === 'input') return [input, input, input];
    return {};
};
document.appendChild = function(ele) {};
document.removeChild = function(ele) {};
document.getElementsByTagName = function(ele) {
    if (ele === 'script') return [script, script];
    if (ele === 'meta') return [meta, meta];
    if (ele === 'head') return [head];
    return [];
};
document.documentElement = function(ele) {};
document.getElementById = function(ele) {
    if (ele === "root-hammerhead-shadow-ui") return {};
    return null;
};
document.addEventListener = function() {};
document.querySelector = function() { return null; };
document.querySelectorAll = function() { return []; };
document.body = document;
"""

recipe_matcher.register(Recipe(
    domain="www.ouyeel.com",
    version_hint="rs6",
    before_exec_hooks=[OUYEEL_DOM_PATCH],
    profile_overrides={
        "location": {
            "href": "https://www.ouyeel.com/steel/search?pageIndex=0&pageSize=50&productType=",
            "pathname": "/steel/search",
            "search": "?pageIndex=0&pageSize=50&productType=",
        },
        "navigator": {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        },
    },
))
