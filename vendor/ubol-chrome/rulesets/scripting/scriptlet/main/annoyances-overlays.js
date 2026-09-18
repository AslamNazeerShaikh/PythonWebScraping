/*******************************************************************************

    uBlock Origin Lite - a comprehensive, MV3-compliant content blocker
    Copyright (C) 2014-present Raymond Hill

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see {http://www.gnu.org/licenses/}.

    Home: https://github.com/gorhill/uBlock

*/

// ruleset: annoyances-overlays

// Important!
// Isolate from global scope

// Start of local scope
(function uBOL_scriptlets() {

/******************************************************************************/

class ArglistParser {
    constructor(separatorChar = ',', mustQuote = false) {
        this.separatorChar = this.actualSeparatorChar = separatorChar;
        this.separatorCode = this.actualSeparatorCode = separatorChar.charCodeAt(0);
        this.mustQuote = mustQuote;
        this.quoteBeg = 0; this.quoteEnd = 0;
        this.argBeg = 0; this.argEnd = 0;
        this.separatorBeg = 0; this.separatorEnd = 0;
        this.transform = false;
        this.failed = false;
        this.reWhitespaceStart = /^\s+/;
        this.reWhitespaceEnd = /(?:^|\S)(\s+)$/;
        this.reOddTrailingEscape = /(?:^|[^\\])(?:\\\\)*\\$/;
        this.reTrailingEscapeChars = /\\+$/;
    }
    nextArg(pattern, beg = 0) {
        const len = pattern.length;
        this.quoteBeg = beg + this.leftWhitespaceCount(pattern.slice(beg));
        this.failed = false;
        const qc = pattern.charCodeAt(this.quoteBeg);
        if ( qc === 0x22 /* " */ || qc === 0x27 /* ' */ || qc === 0x60 /* ` */ ) {
            this.indexOfNextArgSeparator(pattern, qc);
            if ( this.argEnd !== len ) {
                this.quoteEnd = this.argEnd + 1;
                this.separatorBeg = this.separatorEnd = this.quoteEnd;
                this.separatorEnd += this.leftWhitespaceCount(pattern.slice(this.quoteEnd));
                if ( this.separatorEnd === len ) { return this; }
                if ( pattern.charCodeAt(this.separatorEnd) === this.separatorCode ) {
                    this.separatorEnd += 1;
                    return this;
                }
            }
        }
        this.indexOfNextArgSeparator(pattern, this.separatorCode);
        this.separatorBeg = this.separatorEnd = this.argEnd;
        if ( this.separatorBeg < len ) {
            this.separatorEnd += 1;
        }
        this.argEnd -= this.rightWhitespaceCount(pattern.slice(0, this.separatorBeg));
        this.quoteEnd = this.argEnd;
        if ( this.mustQuote ) {
            this.failed = true;
        }
        return this;
    }
    normalizeArg(s, char = '') {
        if ( char === '' ) { char = this.actualSeparatorChar; }
        let out = '';
        let pos = 0;
        while ( (pos = s.lastIndexOf(char)) !== -1 ) {
            out = s.slice(pos) + out;
            s = s.slice(0, pos);
            const match = this.reTrailingEscapeChars.exec(s);
            if ( match === null ) { continue; }
            const tail = (match[0].length & 1) !== 0
                ? match[0].slice(0, -1)
                : match[0];
            out = tail + out;
            s = s.slice(0, -match[0].length);
        }
        if ( out === '' ) { return s; }
        return s + out;
    }
    leftWhitespaceCount(s) {
        const match = this.reWhitespaceStart.exec(s);
        return match === null ? 0 : match[0].length;
    }
    rightWhitespaceCount(s) {
        const match = this.reWhitespaceEnd.exec(s);
        return match === null ? 0 : match[1].length;
    }
    indexOfNextArgSeparator(pattern, separatorCode) {
        this.argBeg = this.argEnd = separatorCode !== this.separatorCode
            ? this.quoteBeg + 1
            : this.quoteBeg;
        this.transform = false;
        if ( separatorCode !== this.actualSeparatorCode ) {
            this.actualSeparatorCode = separatorCode;
            this.actualSeparatorChar = String.fromCharCode(separatorCode);
        }
        while ( this.argEnd < pattern.length ) {
            const pos = pattern.indexOf(this.actualSeparatorChar, this.argEnd);
            if ( pos === -1 ) {
                return (this.argEnd = pattern.length);
            }
            if ( this.reOddTrailingEscape.test(pattern.slice(0, pos)) === false ) {
                return (this.argEnd = pos);
            }
            this.transform = true;
            this.argEnd = pos + 1;
        }
    }
}

class RangeParser {
    constructor(s) {
        this.not = s.charAt(0) === '!';
        if ( this.not ) { s = s.slice(1); }
        if ( s === '' ) { return; }
        const pos = s.indexOf('-');
        if ( pos !== 0 ) {
            this.min = this.max = parseInt(s, 10) || 0;
        }
        if ( pos !== -1 ) {
            this.max = parseInt(s.slice(pos + 1), 10) || Number.MAX_SAFE_INTEGER;
        }
    }
    unbound() {
        return this.min === undefined && this.max === undefined;
    }
    test(v) {
        const n = Math.min(Math.max(Number(v) || 0, 0), Number.MAX_SAFE_INTEGER);
        if ( this.min === this.max ) {
            return (this.min === undefined || n === this.min) !== this.not;
        }
        if ( this.min === undefined ) {
            return (n <= this.max) !== this.not;
        }
        if ( this.max === undefined ) {
            return (n >= this.min) !== this.not;
        }
        return (n >= this.min && n <= this.max) !== this.not;
    }
}

function abortCurrentScript(...args) {
    runAtHtmlElementFn(( ) => {
        abortCurrentScriptFn(...args);
    });
}

function abortCurrentScriptFn(
    target = '',
    needle = '',
    context = ''
) {
    if ( typeof target !== 'string' ) { return; }
    if ( target === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('abort-current-script', target, needle, context);
    const reNeedle = safe.patternToRegex(needle);
    const reContext = safe.patternToRegex(context);
    const thisScript = document.currentScript;
    const exceptionToken = getExceptionTokenFn();
    const scriptTexts = new WeakMap();
    const textContentGetter = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent').get;
    const getScriptText = elem => {
        let text = textContentGetter.call(elem);
        if ( text.trim() !== '' ) { return text; }
        if ( scriptTexts.has(elem) ) { return scriptTexts.get(elem); }
        const [ , mime, content ] = /^data:([^,]*),(.+)$/.exec(elem.src.trim()) ||
            [ '', '', '' ];
        try {
            switch ( true ) {
            case mime.endsWith(';base64'):
                text = self.atob(content);
                break;
            default:
                text = self.decodeURIComponent(content);
                break;
            }
        } catch {
        }
        scriptTexts.set(elem, text);
        return text;
    };
    const validate = ( ) => {
        const e = document.currentScript;
        if ( e instanceof HTMLScriptElement === false ) { return; }
        if ( e === thisScript ) { return; }
        if ( context !== '' && reContext.test(e.src) === false ) { return; }
        if ( safe.logLevel > 1 && context !== '' ) {
            safe.uboLog(logPrefix, `Matched src\n${e.src}`);
        }
        const scriptText = getScriptText(e);
        if ( reNeedle.test(scriptText) === false ) { return; }
        if ( safe.logLevel > 1 ) {
            safe.uboLog(logPrefix, `Matched text\n${scriptText}`);
        }
        safe.uboLog(logPrefix, 'Aborted');
        throw new ReferenceError(exceptionToken);
    };
    let currentValue = trapPropertyFn(target, {
        get: function() {
            validate();
            return currentValue;
        },
        set: function(a) {
            validate();
            currentValue = a;
        }
    }, { canThrow: true });
}

function abortOnPropertyRead(
    chain = ''
) {
    if ( typeof chain !== 'string' ) { return; }
    if ( chain === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('abort-on-property-read', chain);
    const exceptionToken = getExceptionTokenFn();
    const abort = function() {
        safe.uboLog(logPrefix, 'Aborted');
        throw new ReferenceError(exceptionToken);
    };
    const makeProxy = function(owner, chain) {
        const pos = chain.indexOf('.');
        if ( pos === -1 ) {
            const desc = Object.getOwnPropertyDescriptor(owner, chain);
            if ( !desc || desc.get !== abort ) {
                Object.defineProperty(owner, chain, {
                    get: abort,
                    set: function(){}
                });
            }
            return;
        }
        const prop = chain.slice(0, pos);
        let v = owner[prop];
        chain = chain.slice(pos + 1);
        if ( v ) {
            makeProxy(v, chain);
            return;
        }
        const desc = Object.getOwnPropertyDescriptor(owner, prop);
        if ( desc && desc.set !== undefined ) { return; }
        Object.defineProperty(owner, prop, {
            get: function() { return v; },
            set: function(a) {
                v = a;
                if ( a instanceof Object ) {
                    makeProxy(a, chain);
                }
            }
        });
    };
    const owner = window;
    makeProxy(owner, chain);
}

function abortOnPropertyWrite(
    prop = ''
) {
    if ( typeof prop !== 'string' ) { return; }
    if ( prop === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('abort-on-property-write', prop);
    const exceptionToken = getExceptionTokenFn();
    let owner = window;
    for (;;) {
        const pos = prop.indexOf('.');
        if ( pos === -1 ) { break; }
        owner = owner[prop.slice(0, pos)];
        if ( owner instanceof Object === false ) { return; }
        prop = prop.slice(pos + 1);
    }
    delete owner[prop];
    Object.defineProperty(owner, prop, {
        set: function() {
            safe.uboLog(logPrefix, 'Aborted');
            throw new ReferenceError(exceptionToken);
        }
    });
}

function abortOnStackTrace(
    chain = '',
    needle = '',
    ...varargs
) {
    if ( typeof chain !== 'string' ) { return; }
    const safe = safeSelf();
    const needleDetails = safe.initPattern(needle, { canNegate: true });
    const extraArgs = safe.parseVarargs(varargs);
    if ( needle === '' ) { extraArgs.log = 'all'; }
    const makeProxy = function(owner, chain) {
        const pos = chain.indexOf('.');
        if ( pos === -1 ) {
            let v = owner[chain];
            Object.defineProperty(owner, chain, {
                get: function() {
                    const log = safe.logLevel > 1 ? 'all' : 'match';
                    if ( matchesStackTraceFn(needleDetails, log) ) {
                        throw new ReferenceError(getExceptionTokenFn());
                    }
                    return v;
                },
                set: function(a) {
                    const log = safe.logLevel > 1 ? 'all' : 'match';
                    if ( matchesStackTraceFn(needleDetails, log) ) {
                        throw new ReferenceError(getExceptionTokenFn());
                    }
                    v = a;
                },
            });
            return;
        }
        const prop = chain.slice(0, pos);
        let v = owner[prop];
        chain = chain.slice(pos + 1);
        if ( v ) {
            makeProxy(v, chain);
            return;
        }
        const desc = Object.getOwnPropertyDescriptor(owner, prop);
        if ( desc && desc.set !== undefined ) { return; }
        Object.defineProperty(owner, prop, {
            get: function() { return v; },
            set: function(a) {
                v = a;
                if ( a instanceof Object ) {
                    makeProxy(a, chain);
                }
            }
        });
    };
    const owner = window;
    makeProxy(owner, chain);
}

function adjustSetInterval(
    needleArg = '',
    delayArg = '',
    boostArg = ''
) {
    if ( typeof needleArg !== 'string' ) { return; }
    const safe = safeSelf();
    const reNeedle = safe.patternToRegex(needleArg);
    let delay = delayArg !== '*' ? parseInt(delayArg, 10) : -1;
    if ( isNaN(delay) || isFinite(delay) === false ) { delay = 1000; }
    let boost = parseFloat(boostArg);
    boost = isNaN(boost) === false && isFinite(boost)
        ? Math.min(Math.max(boost, 0.001), 50)
        : 0.05;
    self.setInterval = new Proxy(self.setInterval, {
        apply: function(target, thisArg, args) {
            const [ a, b ] = args;
            if (
                (delay === -1 || b === delay) &&
                reNeedle.test(a.toString())
            ) {
                args[1] = b * boost;
            }
            return target.apply(thisArg, args);
        }
    });
}

function adjustSetTimeout(
    needleArg = '',
    delayArg = '',
    boostArg = ''
) {
    if ( typeof needleArg !== 'string' ) { return; }
    const safe = safeSelf();
    const reNeedle = safe.patternToRegex(needleArg);
    let delay = delayArg !== '*' ? parseInt(delayArg, 10) : -1;
    if ( isNaN(delay) || isFinite(delay) === false ) { delay = 1000; }
    let boost = parseFloat(boostArg);
    boost = isNaN(boost) === false && isFinite(boost)
        ? Math.min(Math.max(boost, 0.001), 50)
        : 0.05;
    self.setTimeout = new Proxy(self.setTimeout, {
        apply: function(target, thisArg, args) {
            const [ a, b ] = args;
            if (
                (delay === -1 || b === delay) &&
                reNeedle.test(a.toString())
            ) {
                args[1] = b * boost;
            }
            return target.apply(thisArg, args);
        }
    });
}

function collateFetchArgumentsFn(resource, options) {
    const safe = safeSelf();
    const props = [
        'body', 'cache', 'credentials', 'duplex', 'headers',
        'integrity', 'keepalive', 'method', 'mode', 'priority',
        'redirect', 'referrer', 'referrerPolicy', 'url'
    ];
    const out = {};
    if ( collateFetchArgumentsFn.collateKnownProps === undefined ) {
        collateFetchArgumentsFn.collateKnownProps = (src, out) => {
            for ( const prop of props ) {
                if ( src[prop] === undefined ) { continue; }
                out[prop] = src[prop];
            }
        };
    }
    if (
        typeof resource !== 'object' ||
        safe.Object_toString.call(resource) !== '[object Request]'
    ) {
        out.url = `${resource}`;
    } else {
        let clone;
        try {
            clone = safe.Request_clone.call(resource);
        } catch {
        }
        collateFetchArgumentsFn.collateKnownProps(clone || resource, out);
    }
    if ( typeof options === 'object' && options !== null ) {
        collateFetchArgumentsFn.collateKnownProps(options, out);
    }
    return out;
}

function generateContentFn(trusted, directive) {
    const safe = safeSelf();
    const randomize = len => {
        const chunks = [];
        let textSize = 0;
        do {
            const s = safe.Math_random().toString(36).slice(2);
            chunks.push(s);
            textSize += s.length;
        }
        while ( textSize < len );
        return chunks.join(' ').slice(0, len);
    };
    if ( directive === 'true' ) {
        return randomize(10);
    }
    if ( directive === 'emptyObj' ) {
        return '{}';
    }
    if ( directive === 'emptyArr' ) {
        return '[]';
    }
    if ( directive === 'emptyStr' ) {
        return '';
    }
    if ( directive.startsWith('length:') ) {
        const match = /^length:(\d+)(?:-(\d+))?$/.exec(directive);
        if ( match === null ) { return ''; }
        const min = parseInt(match[1], 10);
        const extent = safe.Math_max(parseInt(match[2], 10) || 0, min) - min;
        const len = safe.Math_min(min + extent * safe.Math_random(), 500000);
        return randomize(len | 0);
    }
    if ( directive.startsWith('war:') ) {
        if ( scriptletGlobals.warOrigin === undefined ) { return ''; }
        return new Promise(resolve => {
            const warOrigin = scriptletGlobals.warOrigin;
            const warName = directive.slice(4);
            const fullpath = [ warOrigin, '/', warName ];
            const warSecret = scriptletGlobals.warSecret;
            if ( warSecret !== undefined ) {
                fullpath.push('?secret=', warSecret);
            }
            const warXHR = new safe.XMLHttpRequest();
            warXHR.responseType = 'text';
            warXHR.onloadend = ev => {
                resolve(ev.target.responseText || '');
            };
            warXHR.open('GET', fullpath.join(''));
            warXHR.send();
        }).catch(( ) => '');
    }
    if ( directive.startsWith('join:') ) {
        const parts = directive.slice(7)
                .split(directive.slice(5, 7))
                .map(a => generateContentFn(trusted, a));
        return parts.some(a => a instanceof Promise)
            ? Promise.all(parts).then(parts => parts.join(''))
            : parts.join('');
    }
    if ( trusted ) {
        return directive;
    }
    return '';
}

function getExceptionTokenFn() {
    const token = getRandomTokenFn();
    const oe = self.onerror;
    self.onerror = function(msg, ...args) {
        if ( typeof msg === 'string' && msg.includes(token) ) { return true; }
        if ( oe instanceof Function ) {
            return oe.call(this, msg, ...args);
        }
    }.bind();
    return token;
}

function getRandomTokenFn() {
    const safe = safeSelf();
    return safe.String_fromCharCode(Date.now() % 26 + 97) +
        safe.Math_floor(safe.Math_random() * 982451653 + 982451653).toString(36);
}

function jsonPrune(
    rawPrunePaths = '',
    rawNeedlePaths = '',
    stackNeedle = '',
    ...varargs
) {
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('json-prune', rawPrunePaths, rawNeedlePaths, stackNeedle);
    const stackNeedleDetails = safe.initPattern(stackNeedle, { canNegate: true });
    const extraArgs = safe.parseVarargs(varargs);
    proxyApplyFn('JSON.parse', function(context) {
        const objBefore = context.reflect();
        if ( rawPrunePaths === '' ) {
            safe.uboLog(logPrefix, safe.JSON_stringify(objBefore, null, 2));
        }
        const objAfter = objectPruneFn(
            objBefore,
            rawPrunePaths,
            rawNeedlePaths,
            stackNeedleDetails,
            extraArgs
        );
        if ( objAfter === undefined ) { return objBefore; }
        safe.uboLog(logPrefix, 'Pruned');
        if ( safe.logLevel > 1 ) {
            safe.uboLog(logPrefix, `After pruning:\n${safe.JSON_stringify(objAfter, null, 2)}`);
        }
        return objAfter;
    });
}

function matchObjectPropertiesFn(propNeedles, ...objs) {
    const safe = safeSelf();
    const matched = [];
    for ( const obj of objs ) {
        if ( obj instanceof Object === false ) { continue; }
        for ( const [ prop, details ] of propNeedles ) {
            let value = obj[prop];
            if ( value === undefined ) { continue; }
            if ( typeof value !== 'string' ) {
                try { value = safe.JSON_stringify(value); }
                catch { }
                if ( typeof value !== 'string' ) { continue; }
            }
            if ( safe.testPattern(details, value) === false ) { return; }
            matched.push(`${prop}: ${value}`);
        }
    }
    return matched;
}

function matchesStackTraceFn(
    needleDetails,
    logLevel = ''
) {
    const safe = safeSelf();
    const exceptionToken = getExceptionTokenFn();
    const error = new safe.Error(exceptionToken);
    const docURL = new URL(self.location.href);
    docURL.hash = '';
    // Normalize stack trace
    const reLine = /(.*?@)?(\S+)(:\d+):\d+\)?$/;
    const lines = [];
    for ( let line of safe.String_split.call(error.stack, /[\n\r]+/) ) {
        if ( line.includes(exceptionToken) ) { continue; }
        line = line.trim();
        const match = safe.RegExp_exec.call(reLine, line);
        if ( match === null ) { continue; }
        let url = match[2];
        if ( url.startsWith('(') ) { url = url.slice(1); }
        if ( url === docURL.href ) {
            url = 'inlineScript';
        } else if ( url.startsWith('<anonymous>') ) {
            url = 'injectedScript';
        }
        let fn = match[1] !== undefined
            ? match[1].slice(0, -1)
            : line.slice(0, match.index).trim();
        if ( fn.startsWith('at') ) { fn = fn.slice(2).trim(); }
        let rowcol = match[3];
        lines.push(' ' + `${fn} ${url}${rowcol}:1`.trim());
    }
    lines[0] = `stackDepth:${lines.length-1}`;
    const stack = lines.join('\t');
    const r = needleDetails.matchAll !== true &&
        safe.testPattern(needleDetails, stack);
    if (
        logLevel === 'all' ||
        logLevel === 'match' && r ||
        logLevel === 'nomatch' && !r
    ) {
        safe.uboLog(stack.replace(/\t/g, '\n'));
    }
    return r;
}

function noEvalIf(
    needle = ''
) {
    if ( typeof needle !== 'string' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('noeval-if', needle);
    const reNeedle = safe.patternToRegex(needle);
    proxyApplyFn('eval', function(context) {
        const { callArgs } = context;
        const a = String(callArgs[0]);
        if ( needle !== '' && reNeedle.test(a) ) {
            safe.uboLog(logPrefix, 'Prevented:\n', a);
            return;
        }
        if ( needle === '' || safe.logLevel > 1 ) {
            safe.uboLog(logPrefix, 'Not prevented:\n', a);
        }
        return context.reflect();
    });
}

function noWindowOpenIf(
    pattern = '',
    delay = '',
    decoy = ''
) {
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('no-window-open-if', pattern, delay, decoy);
    const targetMatchResult = pattern.startsWith('!') === false;
    if ( targetMatchResult === false ) {
        pattern = pattern.slice(1);
    }
    const rePattern = safe.patternToRegex(pattern);
    const autoRemoveAfter = (parseFloat(delay) || 0) * 1000;
    const setTimeout = self.setTimeout;
    const createDecoy = function(tag, urlProp, url) {
        const decoyElem = document.createElement(tag);
        decoyElem[urlProp] = url;
        decoyElem.style.setProperty('height','1px', 'important');
        decoyElem.style.setProperty('position','fixed', 'important');
        decoyElem.style.setProperty('top','-1px', 'important');
        decoyElem.style.setProperty('width','1px', 'important');
        document.body.appendChild(decoyElem);
        setTimeout(( ) => { decoyElem.remove(); }, autoRemoveAfter);
        return decoyElem;
    };
    const noopFunc = function(){};
    proxyApplyFn('open', function open(context) {
        if ( pattern === 'debug' && safe.logLevel !== 0 ) {
            debugger; // eslint-disable-line no-debugger
            return context.reflect();
        }
        const { callArgs } = context;
        const haystack = callArgs.join(' ');
        if ( rePattern.test(haystack) !== targetMatchResult ) {
            if ( safe.logLevel > 1 ) {
                safe.uboLog(logPrefix, `Allowed (${callArgs.join(', ')})`);
            }
            return context.reflect();
        }
        safe.uboLog(logPrefix, `Prevented (${callArgs.join(', ')})`);
        if ( delay === '' ) { return null; }
        if ( decoy === 'blank' ) {
            callArgs[0] = 'about:blank';
            const r = context.reflect();
            setTimeout(( ) => { r.close(); }, autoRemoveAfter);
            return r;
        }
        const decoyElem = decoy === 'obj'
            ? createDecoy('object', 'data', ...callArgs)
            : createDecoy('iframe', 'src', ...callArgs);
        let popup = decoyElem.contentWindow;
        if ( typeof popup === 'object' && popup !== null ) {
            Object.defineProperty(popup, 'closed', { value: false });
        } else {
            popup = new Proxy(self, {
                get: function(target, prop, ...args) {
                    if ( prop === 'closed' ) { return false; }
                    const r = Reflect.get(target, prop, ...args);
                    if ( typeof r === 'function' ) { return noopFunc; }
                    return r;
                },
                set: function(...args) {
                    return Reflect.set(...args);
                },
            });
        }
        if ( safe.logLevel !== 0 ) {
            popup = new Proxy(popup, {
                get: function(target, prop, ...args) {
                    const r = Reflect.get(target, prop, ...args);
                    safe.uboLog(logPrefix, `popup / get ${prop} === ${r}`);
                    if ( typeof r === 'function' ) {
                        return (...args) => { return r.call(target, ...args); };
                    }
                    return r;
                },
                set: function(target, prop, value, ...args) {
                    safe.uboLog(logPrefix, `popup / set ${prop} = ${value}`);
                    return Reflect.set(target, prop, value, ...args);
                },
            });
        }
        return popup;
    });
}

function objectFindOwnerFn(
    root,
    path,
    prune = false
) {
    const safe = safeSelf();
    let owner = root;
    let chain = path;
    for (;;) {
        if ( typeof owner !== 'object' || owner === null  ) { return false; }
        const pos = chain.indexOf('.');
        if ( pos === -1 ) {
            if ( prune === false ) {
                return safe.Object_hasOwn(owner, chain);
            }
            let modified = false;
            if ( chain === '*' ) {
                for ( const key in owner ) {
                    if ( safe.Object_hasOwn(owner, key) === false ) { continue; }
                    delete owner[key];
                    modified = true;
                }
            } else if ( safe.Object_hasOwn(owner, chain) ) {
                delete owner[chain];
                modified = true;
            }
            return modified;
        }
        const prop = chain.slice(0, pos);
        const next = chain.slice(pos + 1);
        let found = false;
        if ( prop === '[-]' && Array.isArray(owner) ) {
            let i = owner.length;
            while ( i-- ) {
                if ( objectFindOwnerFn(owner[i], next) === false ) { continue; }
                owner.splice(i, 1);
                found = true;
            }
            return found;
        }
        if ( prop === '{-}' && owner instanceof Object ) {
            for ( const key of Object.keys(owner) ) {
                if ( objectFindOwnerFn(owner[key], next) === false ) { continue; }
                delete owner[key];
                found = true;
            }
            return found;
        }
        if (
            prop === '[]' && Array.isArray(owner) ||
            prop === '{}' && owner instanceof Object ||
            prop === '*' && owner instanceof Object
        ) {
            for ( const key of Object.keys(owner) ) {
                if (objectFindOwnerFn(owner[key], next, prune) === false ) { continue; }
                found = true;
            }
            return found;
        }
        if ( safe.Object_hasOwn(owner, prop) === false ) { return false; }
        owner = owner[prop];
        chain = chain.slice(pos + 1);
    }
}

function objectPruneFn(
    obj,
    rawPrunePaths,
    rawNeedlePaths,
    stackNeedleDetails = { matchAll: true },
    extraArgs = {}
) {
    if ( typeof rawPrunePaths !== 'string' ) { return; }
    const safe = safeSelf();
    const prunePaths = rawPrunePaths !== ''
        ? safe.String_split.call(rawPrunePaths, / +/)
        : [];
    const needlePaths = prunePaths.length !== 0 && rawNeedlePaths !== ''
        ? safe.String_split.call(rawNeedlePaths, / +/)
        : [];
    if ( stackNeedleDetails.matchAll !== true ) {
        if ( matchesStackTraceFn(stackNeedleDetails, extraArgs.logstack) === false ) {
            return;
        }
    }
    if ( objectPruneFn.mustProcess === undefined ) {
        objectPruneFn.mustProcess = (root, needlePaths) => {
            for ( const needlePath of needlePaths ) {
                if ( objectFindOwnerFn(root, needlePath) === false ) {
                    return false;
                }
            }
            return true;
        };
    }
    if ( prunePaths.length === 0 ) { return; }
    let outcome = 'nomatch';
    if ( objectPruneFn.mustProcess(obj, needlePaths) ) {
        for ( const path of prunePaths ) {
            if ( objectFindOwnerFn(obj, path, true) ) {
                outcome = 'match';
            }
        }
    }
    if ( outcome === 'match' ) { return obj; }
}

function offIdleFn(id) {
    if ( self.requestIdleCallback ) {
        return self.cancelIdleCallback(id);
    }
    return self.cancelAnimationFrame(id);
}

function onIdleFn(fn, options) {
    if ( self.requestIdleCallback ) {
        return self.requestIdleCallback(fn, options);
    }
    return self.requestAnimationFrame(fn);
}

function parsePropertiesToMatchFn(propsToMatch, implicit = '') {
    const safe = safeSelf();
    const needles = new Map();
    if ( propsToMatch === undefined || propsToMatch === '' ) { return needles; }
    const options = { canNegate: true };
    for ( const needle of safe.String_split.call(propsToMatch, /\s+/) ) {
        let [ prop, pattern ] = safe.String_split.call(needle, ':');
        if ( prop === '' ) { continue; }
        if ( pattern !== undefined && /[^$\w -]/.test(prop) ) {
            prop = `${prop}:${pattern}`;
            pattern = undefined;
        }
        if ( pattern !== undefined ) {
            needles.set(prop, safe.initPattern(pattern, options));
        } else if ( implicit !== '' ) {
            needles.set(implicit, safe.initPattern(prop, options));
        }
    }
    return needles;
}

function parseReplaceFn(s) {
    if ( s.charCodeAt(0) !== 0x2F /* / */ ) { return; }
    const parser = new ArglistParser('/');
    parser.nextArg(s, 1);
    let pattern = s.slice(parser.argBeg, parser.argEnd);
    if ( parser.transform ) {
        pattern = parser.normalizeArg(pattern);
    }
    if ( pattern === '' ) { return; }
    parser.nextArg(s, parser.separatorEnd);
    let replacement = s.slice(parser.argBeg, parser.argEnd);
    if ( parser.separatorEnd === parser.separatorBeg ) { return; }
    if ( parser.transform ) {
        replacement = parser.normalizeArg(replacement);
    }
    const flags = s.slice(parser.separatorEnd);
    try {
        return { re: new RegExp(pattern, flags), replacement };
    } catch {
    }
}

function preventAddEventListener(
    type = '',
    pattern = '',
    ...varargs
) {
    const safe = safeSelf();
    const extraArgs = safe.parseVarargs(varargs);
    const logPrefix = safe.makeLogPrefix('prevent-addEventListener', type, pattern);
    const reType = safe.patternToRegex(type, undefined, true);
    const rePattern = safe.patternToRegex(pattern);
    const targetSelector = extraArgs.elements || undefined;
    const elementMatches = elem => {
        if ( targetSelector === 'window' ) { return elem === window; }
        if ( targetSelector === 'document' ) { return elem === document; }
        if ( elem && elem.matches && elem.matches(targetSelector) ) { return true; }
        const elems = Array.from(document.querySelectorAll(targetSelector));
        return elems.includes(elem);
    };
    const elementDetails = elem => {
        if ( elem instanceof Window ) { return 'window'; }
        if ( elem instanceof Document ) { return 'document'; }
        if ( elem instanceof Element === false ) { return '?'; }
        const parts = [];
        // https://github.com/uBlockOrigin/uAssets/discussions/17907#discussioncomment-9871079
        const id = String(elem.id);
        if ( id !== '' ) { parts.push(`#${CSS.escape(id)}`); }
        for ( let i = 0; i < elem.classList.length; i++ ) {
            parts.push(`.${CSS.escape(elem.classList.item(i))}`);
        }
        for ( let i = 0; i < elem.attributes.length; i++ ) {
            const attr = elem.attributes.item(i);
            if ( attr.name === 'id' ) { continue; }
            if ( attr.name === 'class' ) { continue; }
            parts.push(`[${CSS.escape(attr.name)}="${attr.value}"]`);
        }
        return parts.join('');
    };
    const shouldPrevent = (thisArg, type, handler) => {
        const matchesType = safe.RegExp_test(reType, type);
        const matchesHandler = safe.RegExp_test(rePattern, handler);
        const matchesEither = matchesType || matchesHandler;
        const matchesBoth = matchesType && matchesHandler;
        if ( safe.logLevel > 1 && matchesEither ) {
            debugger; // eslint-disable-line no-debugger
        }
        if ( matchesBoth && targetSelector !== undefined ) {
            if ( elementMatches(thisArg) === false ) { return false; }
        }
        return matchesBoth;
    };
    const proxyFn = function(context) {
        const { callArgs, thisArg } = context;
        let t, h;
        try {
            t = String(callArgs[0]);
            if ( typeof callArgs[1] === 'function' ) {
                h = String(safe.Function_toString(callArgs[1]));
            } else if ( typeof callArgs[1] === 'object' && callArgs[1] !== null ) {
                if ( typeof callArgs[1].handleEvent === 'function' ) {
                    h = String(safe.Function_toString(callArgs[1].handleEvent));
                }
            } else {
                h = String(callArgs[1]);
            }
        } catch {
        }
        if ( type === '' && pattern === '' ) {
            safe.uboLog(logPrefix, `Called: ${t}\n${h}\n${elementDetails(thisArg)}`);
        } else if ( shouldPrevent(thisArg, t, h) ) {
            return safe.uboLog(logPrefix, `Prevented: ${t}\n${h}\n${elementDetails(thisArg)}`);
        }
        return context.reflect();
    };
    const protect = owner => {
        const { addEventListener } = owner;
        Object.defineProperty(owner, 'addEventListener', {
            set() { },
            get() { return addEventListener; }
        });
    };
    runAt(( ) => {
        proxyApplyFn('EventTarget.prototype.addEventListener', proxyFn);
        if ( extraArgs.protect ) { protect(EventTarget.prototype); }
        if ( Object.hasOwn(document, 'addEventListener') ) {
            proxyApplyFn('document.addEventListener', proxyFn);
            if ( extraArgs.protect ) { protect(document); }
        }
        if ( Object.hasOwn(window, 'addEventListener') ) {
            proxyApplyFn('window.addEventListener', proxyFn);
            if ( extraArgs.protect ) { protect(window); }
        }
    }, extraArgs.runAt);
}

function preventFetch(...args) {
    preventFetchFn(false, ...args);
}

function preventFetchFn(
    trusted = false,
    propsToMatch = '',
    responseBody = '',
    responseType = '',
    ...varargs
) {
    const safe = safeSelf();
    const setTimeout = self.setTimeout;
    const scriptletName = `${trusted ? 'trusted-' : ''}prevent-fetch`;
    const logPrefix = safe.makeLogPrefix(
        scriptletName,
        propsToMatch,
        responseBody,
        responseType
    );
    const extraArgs = safe.parseVarargs(varargs);
    const propNeedles = parsePropertiesToMatchFn(propsToMatch, 'url');
    const validResponseProps = {
        ok: [ false, true ],
        status: [ 403 ],
        statusText: [ '', 'Not Found' ],
        type: [ 'basic', 'cors', 'default', 'error', 'opaque' ],
    };
    const responseProps = {
        statusText: { value: 'OK' },
    };
    const responseHeaders = {};
    if ( /^\{.*\}$/.test(responseType) ) {
        try {
            Object.entries(JSON.parse(responseType)).forEach(([ p, v ]) => {
                if ( p === 'headers' && trusted ) {
                    Object.assign(responseHeaders, v);
                    return;
                }
                if ( validResponseProps[p] === undefined ) { return; }
                if ( validResponseProps[p].includes(v) === false ) { return; }
                responseProps[p] = { value: v };
            });
        }
        catch { }
    } else if ( responseType !== '' ) {
        if ( validResponseProps.type.includes(responseType) ) {
            responseProps.type = { value: responseType };
        }
    }
    proxyApplyFn('fetch', function fetch(context) {
        const { callArgs } = context;
        const details = collateFetchArgumentsFn(...callArgs);
        if ( safe.logLevel > 1 || propsToMatch === '' && responseBody === '' ) {
            const out = Array.from(Object.entries(details)).map(a => `${a[0]}:${a[1]}`);
            safe.uboLog(logPrefix, `Called: ${out.join('\n')}`);
        }
        if ( propsToMatch === '' && responseBody === '' ) {
            return context.reflect();
        }
        const matched = matchObjectPropertiesFn(propNeedles, details);
        if ( matched === undefined || matched.length === 0 ) {
            return context.reflect();
        }
        return Promise.resolve(generateContentFn(trusted, responseBody)).then(text => {
            safe.uboLog(logPrefix, `Prevented with response "${text}"`);
            const headers = Object.assign({}, responseHeaders);
            if ( headers['content-length'] === undefined ) {
                headers['content-length'] = text.length;
            }
            const response = new Response(text, { headers });
            const props = Object.assign(
                { url: { value: details.url } },
                responseProps
            );
            safe.Object_defineProperties(response, props);
            if ( extraArgs.throttle ) {
                return new Promise(resolve => {
                    setTimeout(( ) => { resolve(response); }, extraArgs.throttle);
                });
            }
            return response;
        });
    });
}

function preventSetInterval(
    needleRaw = '',
    delayRaw = ''
) {
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('prevent-setInterval', needleRaw, delayRaw);
    const needleNot = needleRaw.charAt(0) === '!';
    const reNeedle = safe.patternToRegex(needleNot ? needleRaw.slice(1) : needleRaw);
    const range = new RangeParser(delayRaw);
    proxyApplyFn('setInterval', function(context) {
        const { callArgs } = context;
        const a = callArgs[0] instanceof Function
            ? safe.String(safe.Function_toString(callArgs[0]))
            : safe.String(callArgs[0]);
        const b = callArgs[1];
        if ( needleRaw === '' && range.unbound() ) {
            safe.uboLog(logPrefix, `Called:\n${a}\n${b}`);
            return context.reflect();
        }
        if ( reNeedle.test(a) !== needleNot && range.test(b) ) {
            callArgs[0] = function(){};
            safe.uboLog(logPrefix, `Prevented:\n${a}\n${b}`);
        }
        return context.reflect();
    });
}

function preventSetTimeout(
    needleRaw = '',
    delayRaw = ''
) {
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('prevent-setTimeout', needleRaw, delayRaw);
    const needleNot = needleRaw.charAt(0) === '!';
    const reNeedle = safe.patternToRegex(needleNot ? needleRaw.slice(1) : needleRaw);
    const range = new RangeParser(delayRaw);
    proxyApplyFn('setTimeout', function(context) {
        const { callArgs } = context;
        const a = callArgs[0] instanceof Function
            ? safe.String(safe.Function_toString(callArgs[0]))
            : safe.String(callArgs[0]);
        const b = callArgs[1];
        if ( needleRaw === '' && range.unbound() ) {
            safe.uboLog(logPrefix, `Called:\n${a}\n${b}`);
            return context.reflect();
        }
        if ( reNeedle.test(a) !== needleNot && range.test(b) ) {
            callArgs[0] = function(){};
            safe.uboLog(logPrefix, `Prevented:\n${a}\n${b}`);
        }
        return context.reflect();
    });
}

function preventXhr(...args) {
    preventXhrFn(false, ...args);
}

function preventXhrFn(
    trusted = false,
    propsToMatch = '',
    directive = ''
) {
    if ( typeof propsToMatch !== 'string' ) { return; }
    const safe = safeSelf();
    const scriptletName = trusted ? 'trusted-prevent-xhr' : 'prevent-xhr';
    const logPrefix = safe.makeLogPrefix(scriptletName, propsToMatch, directive);
    const xhrInstances = new WeakMap();
    const propNeedles = parsePropertiesToMatchFn(propsToMatch, 'url');
    const warOrigin = scriptletGlobals.warOrigin;
    const safeDispatchEvent = (xhr, type) => {
        try {
            xhr.dispatchEvent(new Event(type));
        } catch {
        }
    };
    proxyApplyFn('XMLHttpRequest.prototype.open', function(context) {
        const { thisArg, callArgs } = context;
        xhrInstances.delete(thisArg);
        const [ method, url, ...args ] = callArgs;
        if ( warOrigin !== undefined && url.startsWith(warOrigin) ) {
            return context.reflect();
        }
        const haystack = { method, url };
        if ( propsToMatch === '' && directive === '' ) {
            safe.uboLog(logPrefix, `Called: ${safe.JSON_stringify(haystack, null, 2)}`);
            return context.reflect();
        }
        if ( matchObjectPropertiesFn(propNeedles, haystack) ) {
            const xhrDetails = Object.assign(haystack, {
                xhr: thisArg,
                defer: args.length === 0 || !!args[0],
                directive,
                headers: {
                    'date': '',
                    'content-type': '',
                    'content-length': '',
                },
                url: haystack.url,
                props: {
                    response: { value: '' },
                    responseText: { value: '' },
                    responseXML: { value: null },
                },
            });
            xhrInstances.set(thisArg, xhrDetails);
        }
        return context.reflect();
    });
    proxyApplyFn('XMLHttpRequest.prototype.send', function(context) {
        const { thisArg } = context;
        const xhrDetails = xhrInstances.get(thisArg);
        if ( xhrDetails === undefined ) {
            return context.reflect();
        }
        xhrDetails.headers['date'] = (new Date()).toUTCString();
        let xhrText = '';
        switch ( thisArg.responseType ) {
        case 'arraybuffer':
            xhrDetails.props.response.value = new ArrayBuffer(0);
            xhrDetails.headers['content-type'] = 'application/octet-stream';
            break;
        case 'blob':
            xhrDetails.props.response.value = new Blob([]);
            xhrDetails.headers['content-type'] = 'application/octet-stream';
            break;
        case 'document': {
            const parser = new DOMParser();
            const doc = parser.parseFromString('', 'text/html');
            xhrDetails.props.response.value = doc;
            xhrDetails.props.responseXML.value = doc;
            xhrDetails.headers['content-type'] = 'text/html';
            break;
        }
        case 'json':
            xhrDetails.props.response.value = {};
            xhrDetails.props.responseText.value = '{}';
            xhrDetails.headers['content-type'] = 'application/json';
            break;
        default: {
            if ( directive === '' ) { break; }
            xhrText = generateContentFn(trusted, xhrDetails.directive);
            if ( xhrText instanceof Promise ) {
                xhrText = xhrText.then(text => {
                    xhrDetails.props.response.value = text;
                    xhrDetails.props.responseText.value = text;
                });
            } else {
                xhrDetails.props.response.value = xhrText;
                xhrDetails.props.responseText.value = xhrText;
            }
            xhrDetails.headers['content-type'] = 'text/plain';
            break;
        }
        }
        if ( xhrDetails.defer === false ) {
            xhrDetails.headers['content-length'] = `${xhrDetails.props.response.value}`.length;
            Object.defineProperties(xhrDetails.xhr, {
                readyState: { value: 4 },
                responseURL: { value: xhrDetails.url },
                status: { value: 200 },
                statusText: { value: 'OK' },
            });
            Object.defineProperties(xhrDetails.xhr, xhrDetails.props);
            return;
        }
        Promise.resolve(xhrText).then(( ) => xhrDetails).then(details => {
            Object.defineProperties(details.xhr, {
                readyState: { value: 1, configurable: true },
                responseURL: { value: xhrDetails.url },
            });
            safeDispatchEvent(details.xhr, 'readystatechange');
            return details;
        }).then(details => {
            xhrDetails.headers['content-length'] = `${details.props.response.value}`.length;
            Object.defineProperties(details.xhr, {
                readyState: { value: 2, configurable: true },
                status: { value: 200 },
                statusText: { value: 'OK' },
            });
            safeDispatchEvent(details.xhr, 'readystatechange');
            return details;
        }).then(details => {
            Object.defineProperties(details.xhr, {
                readyState: { value: 3, configurable: true },
            });
            Object.defineProperties(details.xhr, details.props);
            safeDispatchEvent(details.xhr, 'readystatechange');
            return details;
        }).then(details => {
            Object.defineProperties(details.xhr, {
                readyState: { value: 4 },
            });
            safeDispatchEvent(details.xhr, 'readystatechange');
            safeDispatchEvent(details.xhr, 'load');
            safeDispatchEvent(details.xhr, 'loadend');
            safe.uboLog(logPrefix, `Prevented with response:\n${details.xhr.response}`);
        });
    });
    proxyApplyFn('XMLHttpRequest.prototype.getResponseHeader', function(context) {
        const { thisArg } = context;
        const xhrDetails = xhrInstances.get(thisArg);
        if ( xhrDetails === undefined || thisArg.readyState < thisArg.HEADERS_RECEIVED ) {
            return context.reflect();
        }
        const headerName = `${context.callArgs[0]}`;
        const value = xhrDetails.headers[headerName.toLowerCase()];
        if ( value !== undefined && value !== '' ) { return value; }
        return null;
    });
    proxyApplyFn('XMLHttpRequest.prototype.getAllResponseHeaders', function(context) {
        const { thisArg } = context;
        const xhrDetails = xhrInstances.get(thisArg);
        if ( xhrDetails === undefined || thisArg.readyState < thisArg.HEADERS_RECEIVED ) {
            return context.reflect();
        }
        const out = [];
        for ( const [ name, value ] of Object.entries(xhrDetails.headers) ) {
            if ( !value ) { continue; }
            out.push(`${name}: ${value}`);
        }
        if ( out.length !== 0 ) { out.push(''); }
        return out.join('\r\n');
    });
}

function proxyApplyFn(
    target = '',
    handler = '',
    options = {}
) {
    let context = globalThis;
    let prop = target;
    for (;;) {
        const pos = prop.indexOf('.');
        if ( pos === -1 ) { break; }
        context = context[prop.slice(0, pos)];
        if ( context instanceof Object === false ) { return; }
        prop = prop.slice(pos+1);
    }
    const fn = context[prop];
    if ( typeof fn !== 'function' ) { return; }
    if ( proxyApplyFn.CtorContext === undefined ) {
        proxyApplyFn.ctorContexts = [];
        proxyApplyFn.CtorContext = class {
            constructor(...args) {
                this.init(...args);
            }
            init(callFn, callArgs) {
                this.callFn = callFn;
                this.callArgs = callArgs;
                return this;
            }
            reflect() {
                const r = Reflect.construct(this.callFn, this.callArgs);
                this.callFn = this.callArgs = this.private = undefined;
                proxyApplyFn.ctorContexts.push(this);
                return r;
            }
            static factory(...args) {
                return proxyApplyFn.ctorContexts.length !== 0
                    ? proxyApplyFn.ctorContexts.pop().init(...args)
                    : new proxyApplyFn.CtorContext(...args);
            }
        };
        proxyApplyFn.applyContexts = [];
        proxyApplyFn.ApplyContext = class {
            constructor(...args) {
                this.init(...args);
            }
            init(callFn, thisArg, callArgs) {
                this.callFn = callFn;
                this.thisArg = thisArg;
                this.callArgs = callArgs;
                return this;
            }
            reflect() {
                const r = Reflect.apply(this.callFn, this.thisArg, this.callArgs);
                this.callFn = this.thisArg = this.callArgs = this.private = undefined;
                proxyApplyFn.applyContexts.push(this);
                return r;
            }
            static factory(...args) {
                return proxyApplyFn.applyContexts.length !== 0
                    ? proxyApplyFn.applyContexts.pop().init(...args)
                    : new proxyApplyFn.ApplyContext(...args);
            }
        };
        proxyApplyFn.isCtor = new Map();
        proxyApplyFn.proxies = new WeakMap();
        if ( (options.skipToString || proxyApplyFn.skipToString) !== true ) {
            proxyApplyFn.nativeToString = Function.prototype.toString;
            const proxiedToString = new Proxy(Function.prototype.toString, {
                apply(target, thisArg) {
                    let proxied = thisArg;
                    for(;;) {
                        const fn = proxyApplyFn.proxies.get(proxied);
                        if ( fn === undefined ) { break; }
                        proxied = fn;
                    }
                    return proxyApplyFn.nativeToString.call(proxied);
                }
            });
            proxyApplyFn.proxies.set(proxiedToString, proxyApplyFn.nativeToString);
            Function.prototype.toString = proxiedToString;
        }
    }
    if ( proxyApplyFn.isCtor.has(target) === false ) {
        proxyApplyFn.isCtor.set(target, fn.prototype?.constructor === fn);
    }
    const proxyDetails = {
        apply(target, thisArg, args) {
            return handler(proxyApplyFn.ApplyContext.factory(target, thisArg, args));
        }
    };
    if ( proxyApplyFn.isCtor.get(target) ) {
        proxyDetails.construct = function(target, args) {
            return handler(proxyApplyFn.CtorContext.factory(target, args));
        };
    }
    const proxiedTarget = new Proxy(fn, proxyDetails);
    proxyApplyFn.proxies.set(proxiedTarget, fn);
    context[prop] = proxiedTarget;
}

function removeAttr(
    rawToken = '',
    rawSelector = '',
    behavior = '',
    ...varargs
) {
    if ( typeof rawToken !== 'string' ) { return; }
    if ( rawToken === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('remove-attr',
        rawToken, rawSelector, behavior, ...varargs
    );
    const tokens = safe.String_split.call(rawToken, /\s*\|\s*/);
    const selector = tokens.map(a => {
        const b = CSS.escape(a);
        return rawSelector.includes(`[${b}]`) ? rawSelector : `${rawSelector}[${b}]`;
    }).join(',');
    const lazily = /\basap\b/.test(behavior) === false;
    const options = safe.parseVarargs(varargs);
    if ( safe.logLevel > 1 ) {
        safe.uboLog(logPrefix, `Target selector:\n\t${selector}`);
    }
    const rmattrFromNode = node => {
        for ( const attr of tokens ) {
            if ( node.hasAttribute(attr) === false ) { continue; }
            node.removeAttribute(attr);
            safe.uboLog(logPrefix, `Removed attribute '${attr}'`);
        }
    };
    const rmattr = nodes => {
        for ( const node of nodes ?? document.querySelectorAll(selector) ) {
            rmattrFromNode(node);
        }
    };
    const rmAttrLazily = ( ) => {
        if ( rmAttrLazily.timer !== undefined ) { return; }
        rmAttrLazily.timer = onIdleFn(( ) => {
            rmAttrLazily.timer = undefined;
            rmattr();
        }, { timeout: 17 });
    };
    const mutationHandler = mutations => {
        for ( const { addedNodes, removedNodes } of mutations ) {
            for ( const node of addedNodes ) {
                if ( node.nodeType !== 1 ) { continue; }
                if ( lazily ) { return rmAttrLazily(); }
                if ( node.matches(selector) ) {
                    rmattrFromNode(node);
                }
                if ( node.childElementCount ) {
                    rmattr(node.querySelectorAll(selector));
                }
            }
            if ( lazily ) { return; }
            for ( const node of removedNodes ) {
                if ( node.nodeType !== 1 ) { continue; }
                if ( node.matches(selector) ) {
                    rmattrFromNode(node);
                }
            }
        }
    };
    const stop = ( ) => {
        if ( start.observer ) {
            start.observer.disconnect();
            start.observer = undefined;
        }
        if ( rmAttrLazily.timer ) {
            offIdleFn(rmAttrLazily.timer);
            rmAttrLazily.timer = undefined;
        }
        if ( safe.logLevel > 1 ) {
            safe.uboLog(logPrefix, 'Quitting');
        }
    };
    const start = ( ) => {
        rmattr();
        if ( /\bstay\b/.test(behavior) === false ) {
            if ( options.quitAfter === undefined ) { return; }
        }
        start.observer = new MutationObserver(mutationHandler);
        start.observer.observe(document, {
            attributes: true,
            attributeFilter: tokens,
            childList: true,
            subtree: true,
        });
        if ( options.quitAfter ) {
            runAt(( ) => {
                self.setTimeout(stop, options.quitAfter * 1000);
            }, 'load');
        }
    };
    runAt(( ) => { start(); }, safe.String_split.call(behavior, /\s+/));
}

function runAt(fn, when) {
    const intFromReadyState = state => {
        const targets = {
            'loading': 1, 'asap': 1,
            'interactive': 2, 'end': 2, '2': 2,
            'complete': 3, 'idle': 3, '3': 3,
        };
        const tokens = Array.isArray(state) ? state : [ state ];
        for ( const token of tokens ) {
            const prop = `${token}`;
            if ( Object.hasOwn(targets, prop) === false ) { continue; }
            return targets[prop];
        }
        return 0;
    };
    const runAt = intFromReadyState(when);
    if ( intFromReadyState(document.readyState) >= runAt ) {
        fn(); return;
    }
    const onStateChange = ( ) => {
        if ( intFromReadyState(document.readyState) < runAt ) { return; }
        fn();
        safe.removeEventListener.apply(document, args);
    };
    const safe = safeSelf();
    const args = [ 'readystatechange', onStateChange, { capture: true } ];
    safe.addEventListener.apply(document, args);
}

function runAtHtmlElementFn(fn) {
    if ( document.documentElement ) {
        fn();
        return;
    }
    const observer = new MutationObserver(( ) => {
        observer.disconnect();
        fn();
    });
    observer.observe(document, { childList: true });
}

function safeSelf() {
    if ( safeSelf.safe ) {
        return safeSelf.safe;
    }
    const self = globalThis;
    const safe = {
        'Array_from': Array.from,
        'Error': self.Error,
        'Function_toString': Function.prototype.call.bind(self.Function.prototype.toString),
        'Math_floor': Math.floor,
        'Math_max': Math.max,
        'Math_min': Math.min,
        'Math_random': Math.random,
        'Object': Object,
        'Object_defineProperty': Object.defineProperty.bind(Object),
        'Object_defineProperties': Object.defineProperties.bind(Object),
        'Object_fromEntries': Object.fromEntries.bind(Object),
        'Object_getOwnPropertyDescriptor': Object.getOwnPropertyDescriptor.bind(Object),
        'Object_hasOwn': Object.hasOwn.bind(Object),
        'Object_toString': Object.prototype.toString,
        'RegExp': self.RegExp,
        'RegExp_test': Function.prototype.call.bind(self.RegExp.prototype.test),
        'RegExp_exec': self.RegExp.prototype.exec,
        'Request_clone': self.Request.prototype.clone,
        'String': self.String,
        'String_fromCharCode': String.fromCharCode,
        'String_split': String.prototype.split,
        'XMLHttpRequest': self.XMLHttpRequest,
        'addEventListener': self.EventTarget.prototype.addEventListener,
        'removeEventListener': self.EventTarget.prototype.removeEventListener,
        'fetch': self.fetch,
        'JSON': self.JSON,
        'JSON_parse': Function.prototype.call.bind(self.JSON.parse, self.JSON),
        'JSON_stringify': Function.prototype.call.bind(self.JSON.stringify, self.JSON),
        'log': console.log.bind(console),
        // Properties
        logLevel: 0,
        // Methods
        makeLogPrefix(...args) {
            return this.sendToLogger && `[${args.join(' \u205D ')}]` || '';
        },
        uboLog(...args) {
            if ( this.sendToLogger === undefined ) { return; }
            if ( args === undefined || args[0] === '' ) { return; }
            return this.sendToLogger('info', ...args);
            
        },
        uboErr(...args) {
            if ( this.sendToLogger === undefined ) { return; }
            if ( args === undefined || args[0] === '' ) { return; }
            return this.sendToLogger('error', ...args);
        },
        escapeRegexChars(s) {
            return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        },
        initPattern(pattern, options = {}) {
            if ( pattern === '' ) {
                return { matchAll: true, expect: true };
            }
            const expect = (options.canNegate !== true || pattern.startsWith('!') === false);
            if ( expect === false ) {
                pattern = pattern.slice(1);
            }
            const match = /^\/(.+)\/([gimsu]*)$/.exec(pattern);
            if ( match !== null ) {
                return {
                    re: new this.RegExp(
                        match[1],
                        match[2] || options.flags
                    ),
                    expect,
                };
            }
            if ( options.flags !== undefined ) {
                return {
                    re: new this.RegExp(this.escapeRegexChars(pattern),
                        options.flags
                    ),
                    expect,
                };
            }
            return { pattern, expect };
        },
        testPattern(details, haystack) {
            if ( details.matchAll ) { return true; }
            if ( details.re ) {
                return this.RegExp_test(details.re, haystack) === details.expect;
            }
            return haystack.includes(details.pattern) === details.expect;
        },
        patternToRegex(pattern, flags = undefined, verbatim = false) {
            if ( pattern === '' ) { return /^/; }
            const match = /^\/(.+)\/([gimsu]*)$/.exec(pattern);
            if ( match === null ) {
                const reStr = this.escapeRegexChars(pattern);
                return new RegExp(verbatim ? `^${reStr}$` : reStr, flags);
            }
            try {
                return new RegExp(match[1], match[2] || undefined);
            }
            catch {
            }
            return /^/;
        },
        parseVarargs(varargs) {
            const entries = varargs.reduce((out, v, i, a) => {
                if ( i & 1 ) { return out; }
                const rawValue = a[i+1];
                const value = /^\d+$/.test(rawValue)
                    ? parseInt(rawValue, 10)
                    : rawValue;
                out.push([ a[i], value ]);
                return out;
            }, []);
            return this.Object_fromEntries(entries);
        },
    };
    safeSelf.safe = safe;
    if ( scriptletGlobals.bcSecret === undefined ) { return safe; }
    // This is executed only when the logger is opened
    safe.logLevel = scriptletGlobals.logLevel || 1;
    let lastLogType = '';
    let lastLogText = '';
    let lastLogTime = 0;
    safe.toLogText = (type, ...args) => {
        if ( args.length === 0 ) { return; }
        const text = `[${document.location.hostname || document.location.href}]${args.join(' ')}`;
        if ( text === lastLogText && type === lastLogType ) {
            if ( (Date.now() - lastLogTime) < 5000 ) { return; }
        }
        lastLogType = type;
        lastLogText = text;
        lastLogTime = Date.now();
        return text;
    };
    try {
        const bc = new self.BroadcastChannel(scriptletGlobals.bcSecret);
        let bcBuffer = [];
        safe.sendToLogger = (type, ...args) => {
            const text = safe.toLogText(type, ...args);
            if ( text === undefined ) { return; }
            if ( bcBuffer === undefined ) {
                return bc.postMessage({ what: 'messageToLogger', type, text });
            }
            bcBuffer.push({ type, text });
        };
        bc.onmessage = ev => {
            const msg = ev.data;
            switch ( msg ) {
            case 'iamready!':
                if ( bcBuffer === undefined ) { break; }
                bcBuffer.forEach(({ type, text }) =>
                    bc.postMessage({ what: 'messageToLogger', type, text })
                );
                bcBuffer = undefined;
                break;
            case 'setScriptletLogLevelToOne':
                safe.logLevel = 1;
                break;
            case 'setScriptletLogLevelToTwo':
                safe.logLevel = 2;
                break;
            }
        };
        bc.postMessage('areyouready?');
    } catch {
        safe.sendToLogger = (type, ...args) => {
            const text = safe.toLogText(type, ...args);
            if ( text === undefined ) { return; }
            safe.log(`uBO ${text}`);
        };
    }
    return safe;
}

function setConstant(
    ...args
) {
    setConstantFn(false, ...args);
}

function setConstantFn(
    trusted = false,
    chain = '',
    rawValue = '',
    ...varargs
) {
    if ( chain === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('set-constant', chain, rawValue);
    const extraArgs = safe.parseVarargs(varargs);
    function setConstant(chain, rawValue) {
        const trappedProp = (( ) => {
            const pos = chain.lastIndexOf('.');
            if ( pos === -1 ) { return chain; }
            return chain.slice(pos+1);
        })();
        const cloakFunc = fn => {
            safe.Object_defineProperty(fn, 'name', { value: trappedProp });
            return new Proxy(fn, {
                defineProperty(target, prop) {
                    if ( prop !== 'toString' ) {
                        return Reflect.defineProperty(...arguments);
                    }
                    return true;
                },
                deleteProperty(target, prop) {
                    if ( prop !== 'toString' ) {
                        return Reflect.deleteProperty(...arguments);
                    }
                    return true;
                },
                get(target, prop) {
                    if ( prop === 'toString' ) {
                        return function() {
                            return `function ${trappedProp}() { [native code] }`;
                        }.bind(null);
                    }
                    return Reflect.get(...arguments);
                },
            });
        };
        if ( trappedProp === '' ) { return; }
        const thisScript = document.currentScript;
        let normalValue = validateConstantFn(trusted, rawValue, extraArgs);
        if ( rawValue === 'noopFunc' || rawValue === 'trueFunc' || rawValue === 'falseFunc' ) {
            normalValue = cloakFunc(normalValue);
        }
        let aborted = false;
        const mustAbort = function(v) {
            if ( trusted ) { return false; }
            if ( aborted ) { return true; }
            aborted =
                (v !== undefined && v !== null) &&
                (normalValue !== undefined && normalValue !== null) &&
                (typeof v !== typeof normalValue);
            if ( aborted ) {
                safe.uboLog(logPrefix, `Aborted because value set to ${v}`);
            }
            return aborted;
        };
        // https://github.com/uBlockOrigin/uBlock-issues/issues/156
        //   Support multiple trappers for the same property.
        const trapProp = function(owner, prop, configurable, handler) {
            if ( handler.init(configurable ? owner[prop] : normalValue) === false ) { return; }
            const odesc = safe.Object_getOwnPropertyDescriptor(owner, prop);
            let prevGetter, prevSetter;
            if ( odesc instanceof safe.Object ) {
                owner[prop] = normalValue;
                if ( odesc.get instanceof Function ) {
                    prevGetter = odesc.get;
                }
                if ( odesc.set instanceof Function ) {
                    prevSetter = odesc.set;
                }
            }
            try {
                safe.Object_defineProperty(owner, prop, {
                    configurable,
                    get() {
                        if ( prevGetter !== undefined ) {
                            prevGetter();
                        }
                        return handler.getter();
                    },
                    set(a) {
                        if ( prevSetter !== undefined ) {
                            prevSetter(a);
                        }
                        handler.setter(a);
                    }
                });
                safe.uboLog(logPrefix, 'Trap installed');
            } catch(ex) {
                safe.uboErr(logPrefix, ex);
            }
        };
        const trapChain = function(owner, chain) {
            const pos = chain.indexOf('.');
            if ( pos === -1 ) {
                trapProp(owner, chain, false, {
                    v: undefined,
                    init: function(v) {
                        if ( mustAbort(v) ) { return false; }
                        this.v = v;
                        return true;
                    },
                    getter: function() {
                        if ( document.currentScript === thisScript ) {
                            return this.v;
                        }
                        safe.uboLog(logPrefix, 'Property read');
                        return normalValue;
                    },
                    setter: function(a) {
                        if ( mustAbort(a) === false ) { return; }
                        normalValue = a;
                    }
                });
                return;
            }
            const prop = chain.slice(0, pos);
            const v = owner[prop];
            chain = chain.slice(pos + 1);
            if ( v instanceof safe.Object || typeof v === 'object' && v !== null ) {
                trapChain(v, chain);
                return;
            }
            trapProp(owner, prop, true, {
                v: undefined,
                init: function(v) {
                    this.v = v;
                    return true;
                },
                getter: function() {
                    return this.v;
                },
                setter: function(a) {
                    this.v = a;
                    if ( a instanceof safe.Object ) {
                        trapChain(a, chain);
                    }
                }
            });
        };
        trapChain(window, chain);
    }
    runAt(( ) => {
        setConstant(chain, rawValue);
    }, extraArgs.runAt);
}

function trapPropertyFn(propChain, handler, options = {}) {
    if ( propChain === '' ) { return; }
    let owner = self;
    let prop = propChain;
    for (;;) {
        const pos = prop.indexOf('.');
        if ( pos === -1 ) { break; }
        owner = owner[prop.slice(0, pos)];
        if ( owner instanceof Object === false ) { return; }
        prop = prop.slice(pos + 1);
    }
    const safe = safeSelf();
    if ( trapPropertyFn.db === undefined ) {
        trapPropertyFn.db = new WeakMap();
        trapPropertyFn.entryFromContext = (owner, prop) => {
            const handlers = trapPropertyFn.db.get(owner);
            return handlers?.get(prop);
        };
        trapPropertyFn.getter = (owner, prop) => {
            const entry = trapPropertyFn.entryFromContext(owner, prop);
            if ( entry === undefined ) { return; }
            let r = entry.value;
            for ( const desc of entry.stack ) {
                try { r = desc.get(); } catch (e) {
                    if ( entry.canThrow ) { throw e; }
                }
            }
            return r;
        };
        trapPropertyFn.setter = (owner, prop, value) => {
            const entry = trapPropertyFn.entryFromContext(owner, prop);
            if ( entry === undefined ) { return; }
            entry.value = value;
            for ( const desc of entry.stack ) {
                try { desc.set(value); } catch (e) {
                    if ( entry.canThrow ) { throw e; }
                }
            }
        };
    }
    const { db } = trapPropertyFn;
    const handlers = db.get(owner) || new Map();
    if ( handlers.size === 0 ) {
        db.set(owner, handlers);
    }
    const entry = handlers.get(prop) || {
        value: owner[prop],
        stack: [],
    };
    entry.stack.push(handler);
    if ( entry.stack.length > 1 ) { return entry.value; }
    Object.assign(entry, options);
    handlers.set(prop, entry);
    const desc = safe.Object_getOwnPropertyDescriptor(owner, prop);
    if ( desc instanceof safe.Object ) {
        if ( desc.get || desc.set ) {
            entry.stack.push(desc);
        }
    }
    try {
        safe.Object_defineProperty(owner, prop, {
            get() {
                return trapPropertyFn.getter(owner, prop);
            },
            set(value) {
                trapPropertyFn.setter(owner, prop, value);
            }
        });
    } catch {
    }
    return entry.value;
}

function trustedReplaceArgument(
    propChain = '',
    argposRaw = '',
    argraw = '',
    ...varargs
) {
    if ( propChain === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('trusted-replace-argument', propChain, argposRaw, argraw);
    const argoffset = parseInt(argposRaw, 10) || 0;
    const extraArgs = safe.parseVarargs(varargs);
    let replacer;
    if ( argraw.startsWith('repl:/') ) {
        const parsed = parseReplaceFn(argraw.slice(5));
        if ( parsed === undefined ) { return; }
        replacer = arg => `${arg}`.replace(replacer.re, replacer.replacement);
        Object.assign(replacer, parsed);
    } else if ( argraw.startsWith('add:') ) {
        const delta = parseFloat(argraw.slice(4));
        if ( isNaN(delta) ) { return; }
        replacer = arg => Number(arg) + delta;
    } else {
        const value = validateConstantFn(true, argraw, extraArgs);
        replacer = ( ) => value;
    }
    const reCondition = extraArgs.condition
        ? safe.patternToRegex(`${extraArgs.condition}`)
        : /^/;
    const getArg = context => {
        if ( argposRaw === 'this' ) { return context.thisArg; }
        const { callArgs } = context;
        const argpos = argoffset >= 0 ? argoffset : callArgs.length - argoffset;
        if ( argpos < 0 || argpos >= callArgs.length ) { return; }
        context.private = { argpos };
        return callArgs[argpos];
    };
    const setArg = (context, value) => {
        if ( argposRaw === 'this' ) {
            if ( value !== context.thisArg ) {
                context.thisArg = value;
            }
        } else if ( context.private ) {
            context.callArgs[context.private.argpos] = value;
        }
    };
    proxyApplyFn(propChain, function(context) {
        if ( argposRaw === '' ) {
            safe.uboLog(logPrefix, `Arguments:\n${context.callArgs.join('\n')}`);
            return context.reflect();
        }
        const argBefore = getArg(context);
        if ( extraArgs.condition !== undefined ) {
            if ( safe.RegExp_test(reCondition, argBefore) === false ) {
                return context.reflect();
            }
        }
        const argAfter = replacer(argBefore);
        if ( argAfter !== argBefore ) {
            setArg(context, argAfter);
            safe.uboLog(logPrefix, `Replaced argument:\nBefore: ${JSON.stringify(argBefore)}\nAfter: ${argAfter}`);
        }
        return context.reflect();
    });
}

function trustedReplaceOutboundText(
    propChain = '',
    rawPattern = '',
    rawReplacement = '',
    ...varargs
) {
    if ( propChain === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('trusted-replace-outbound-text', propChain, rawPattern, rawReplacement, ...varargs);
    const rePattern = safe.patternToRegex(rawPattern);
    const replacement = rawReplacement.startsWith('json:')
        ? safe.JSON_parse(rawReplacement.slice(5))
        : rawReplacement;
    const extraArgs = safe.parseVarargs(varargs);
    const reCondition = safe.patternToRegex(extraArgs.condition || '');
    proxyApplyFn(propChain, function(context) {
        const encodedTextBefore = context.reflect();
        let textBefore = encodedTextBefore;
        if ( extraArgs.encoding === 'base64' ) {
            try { textBefore = self.atob(encodedTextBefore); }
            catch { return encodedTextBefore; }
        }
        if ( rawPattern === '' ) {
            safe.uboLog(logPrefix, 'Decoded outbound text:\n', textBefore);
            return encodedTextBefore;
        }
        reCondition.lastIndex = 0;
        if ( reCondition.test(textBefore) === false ) { return encodedTextBefore; }
        const textAfter = textBefore.replace(rePattern, replacement);
        if ( textAfter === textBefore ) { return encodedTextBefore; }
        safe.uboLog(logPrefix, 'Matched and replaced');
        if ( safe.logLevel > 1 ) {
            safe.uboLog(logPrefix, 'Modified decoded outbound text:\n', textAfter);
        }
        let encodedTextAfter = textAfter;
        if ( extraArgs.encoding === 'base64' ) {
            encodedTextAfter = self.btoa(textAfter);
        }
        return encodedTextAfter;
    });
}

function trustedReplaceXhrResponse(
    pattern = '',
    replacement = '',
    propsToMatch = '',
    ...varargs
) {
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('trusted-replace-xhr-response', pattern, replacement, propsToMatch);
    const xhrInstances = new WeakMap();
    if ( pattern === '*' ) { pattern = '.*'; }
    const rePattern = safe.patternToRegex(pattern);
    const propNeedles = parsePropertiesToMatchFn(propsToMatch, 'url');
    const extraArgs = safe.parseVarargs(varargs);
    const reIncludes = extraArgs.includes ? safe.patternToRegex(extraArgs.includes) : null;
    self.XMLHttpRequest = class extends self.XMLHttpRequest {
        open(method, url, ...args) {
            const outerXhr = this;
            const xhrDetails = { method, url };
            let outcome = 'match';
            if ( propNeedles.size !== 0 ) {
                if ( matchObjectPropertiesFn(propNeedles, xhrDetails) === undefined ) {
                    outcome = 'nomatch';
                }
            }
            if ( outcome === 'match' ) {
                if ( safe.logLevel > 1 ) {
                    safe.uboLog(logPrefix, `Matched "propsToMatch"`);
                }
                xhrInstances.set(outerXhr, xhrDetails);
            }
            return super.open(method, url, ...args);
        }
        get response() {
            const innerResponse = super.response;
            const xhrDetails = xhrInstances.get(this);
            if ( xhrDetails === undefined ) {
                return innerResponse;
            }
            const responseLength = typeof innerResponse === 'string'
                ? innerResponse.length
                : undefined;
            if ( xhrDetails.lastResponseLength !== responseLength ) {
                xhrDetails.response = undefined;
                xhrDetails.lastResponseLength = responseLength;
            }
            if ( xhrDetails.response !== undefined ) {
                return xhrDetails.response;
            }
            if ( typeof innerResponse !== 'string' ) {
                return (xhrDetails.response = innerResponse);
            }
            if ( reIncludes && reIncludes.test(innerResponse) === false ) {
                return (xhrDetails.response = innerResponse);
            }
            const textBefore = innerResponse;
            const textAfter = textBefore.replace(rePattern, replacement);
            if ( textAfter !== textBefore ) {
                safe.uboLog(logPrefix, 'Match');
            }
            return (xhrDetails.response = textAfter);
        }
        get responseText() {
            const response = this.response;
            if ( typeof response !== 'string' ) {
                return super.responseText;
            }
            return response;
        }
    };
}

function trustedSetConstant(
    ...args
) {
    setConstantFn(true, ...args);
}

function trustedSuppressNativeMethod(
    methodPath = '',
    signature = '',
    how = '',
    stack = ''
) {
    if ( methodPath === '' ) { return; }
    const safe = safeSelf();
    const logPrefix = safe.makeLogPrefix('trusted-suppress-native-method', methodPath, signature, how, stack);
    const signatureArgs = safe.String_split.call(signature, /\s*\|\s*/).map(v => {
        if ( /^".*"$/.test(v) ) {
            return { type: 'pattern', re: safe.patternToRegex(v.slice(1, -1)) };
        }
        if ( /^\/.+\/$/.test(v) ) {
            return { type: 'pattern', re: safe.patternToRegex(v) };
        }
        if ( v === 'false' ) {
            return { type: 'exact', value: false };
        }
        if ( v === 'true' ) {
            return { type: 'exact', value: true };
        }
        if ( v === 'null' ) {
            return { type: 'exact', value: null };
        }
        if ( v === 'undefined' ) {
            return { type: 'exact', value: undefined };
        }
    });
    const stackNeedle = safe.initPattern(stack, { canNegate: true });
    proxyApplyFn(methodPath, function(context) {
        const { callArgs } = context;
        if ( signature === '' ) {
            safe.uboLog(logPrefix, `Arguments:\n${callArgs.join('\n')}`);
            return context.reflect();
        }
        for ( let i = 0; i < signatureArgs.length; i++ ) {
            const signatureArg = signatureArgs[i];
            if ( signatureArg === undefined ) { continue; }
            const targetArg = i < callArgs.length ? callArgs[i] : undefined;
            if ( signatureArg.type === 'exact' ) {
                if ( targetArg !== signatureArg.value ) {
                    return context.reflect();
                }
            }
            if ( signatureArg.type === 'pattern' ) {
                if ( safe.RegExp_test(signatureArg.re, targetArg) === false ) {
                    return context.reflect();
                }
            }
        }
        if ( stackNeedle.matchAll !== true ) {
            const logLevel = safe.logLevel > 1 ? 'all' : '';
            if ( matchesStackTraceFn(stackNeedle, logLevel) === false ) {
                return context.reflect();
            }
        }
        if ( how === 'debug' ) {
            debugger; // eslint-disable-line no-debugger
            return context.reflect();
        }
        safe.uboLog(logPrefix, `Suppressed:\n${callArgs.join('\n')}`);
        if ( how === 'abort' ) {
            throw new ReferenceError();
        }
    });
}

function validateConstantFn(trusted, raw, extraArgs = {}) {
    const safe = safeSelf();
    let value;
    if ( raw === 'undefined' ) {
        value = undefined;
    } else if ( raw === 'false' ) {
        value = false;
    } else if ( raw === 'true' ) {
        value = true;
    } else if ( raw === 'null' ) {
        value = null;
    } else if ( raw === "''" || raw === '' ) {
        value = '';
    } else if ( raw === '[]' || raw === 'emptyArr' ) {
        value = [];
    } else if ( raw === '{}' || raw === 'emptyObj' ) {
        value = {};
    } else if ( raw === 'noopFunc' ) {
        value = function(){};
    } else if ( raw === 'trueFunc' ) {
        value = function(){ return true; };
    } else if ( raw === 'falseFunc' ) {
        value = function(){ return false; };
    } else if ( raw === 'throwFunc' ) {
        value = function(){ throw ''; };
    } else if ( /^-?\d+$/.test(raw) ) {
        value = parseInt(raw);
        if ( isNaN(raw) ) { return; }
        if ( Math.abs(raw) > 0x7FFF ) { return; }
    } else if ( trusted ) {
        if ( raw.startsWith('json:') ) {
            try { value = safe.JSON_parse(raw.slice(5)); } catch { return; }
        } else if ( raw.startsWith('{') && raw.endsWith('}') ) {
            try { value = safe.JSON_parse(raw).value; } catch { return; }
        }
    } else {
        return;
    }
    if ( extraArgs.as !== undefined ) {
        if ( extraArgs.as === 'function' ) {
            return ( ) => value;
        } else if ( extraArgs.as === 'callback' ) {
            return ( ) => (( ) => value);
        } else if ( extraArgs.as === 'resolved' ) {
            return Promise.resolve(value);
        } else if ( extraArgs.as === 'rejected' ) {
            return Promise.reject(value);
        }
    }
    return value;
}

/******************************************************************************/

const scriptletGlobals = {}; // eslint-disable-line

const $hasHostnames$ = true;
const $hasEntities$ = true;
const $hasAncestors$ = true;
const $hasRegexes$ = false;

/******************************************************************************/

const entries = (( ) => {
    const docloc = document.location;
    const origins = [ docloc.origin ];
    if ( docloc.ancestorOrigins ) {
        origins.push(...docloc.ancestorOrigins);
    }
    return origins.map((origin, i) => {
        const beg = origin.indexOf('://');
        if ( beg === -1 ) { return; }
        const hn1 = origin.slice(beg+3)
        const end = hn1.indexOf(':');
        const hn2 = end === -1 ? hn1 : hn1.slice(0, end);
        if ( hn2.length === 0 ) { return; }
        const hns = [ hn2 ];
        for ( let pos = 0; ; ) {
            pos = hn2.indexOf('.', pos) + 1;
            if ( pos === 0 ) { break; }
            hns.push(hn2.slice(pos));
        }
        hns.push('*');
        const ens = [];
        if ( $hasEntities$ ) {
            for ( let hn of hns ) {
                for (;;) {
                    const pos = hn.lastIndexOf('.');
                    if ( pos === -1 ) { break; }
                    hn = hn.slice(0, pos);
                    ens.push(`${hn}.*`);
                }
            }
            ens.sort((a, b) => {
                const d = b.length - a.length;
                if ( d !== 0 ) { return d; }
                return a > b ? -1 : 1;
            });
        }
        return { hns, ens, i };
    }).filter(a => a);
})();
if ( entries.length === 0 ) { return; }

const todo = new Set();

if ( $hasHostnames$ ) {
    const $scriptletHostnames$ = /* 2109 */ ["x.com","xe.gr","anix.*","clk.sh","ddys.*","dood.*","epn.bz","evz.ro","ft.com","hqq.to","hqq.tv","kmo.to","mbs.jp","mio.to","netu.*","rp5.by","sgd.de","shz.al","t3.com","tfp.is","ttv.pl","tvn.pl","voe.sx","wjx.cn","xtv.cz","1mg.com","app.com","appd.at","bbc.com","bflix.*","bold.dk","c315.cn","cbr.com","cine.to","clk.ink","cnn.com","coag.pl","csid.ro","dnj.com","doods.*","edn.com","gats.io","gmx.com","humo.be","ibps.in","ijr.com","itvn.pl","jfdb.jp","kwik.cx","lifo.gr","mdpr.jp","med1.de","mgsm.pl","onna.kr","pnj.com","pobre.*","rgj.com","sbot.cf","t3.chat","tvn7.pl","veev.to","vox.com","vsco.co","vtbe.to","wjx.top","ydr.com","10tv.com","2219.net","9tsu.vip","abola.pt","allen.in","arras.io","arrax.io","asiatv.*","bcs16.ro","blikk.hu","citas.in","cmg24.pl","cnki.net","daum.net","delfi.lt","dngz.net","dooood.*","embed.su","emol.com","espn.com","flixhq.*","gakki.me","glam.com","hemas.pl","hk01.com","j91.asia","jetv.xyz","jpnn.com","khou.com","kukaj.io","libgen.*","likey.me","mhwg.org","nsmb.com","ntv.cx>>","pisr.org","poedb.tw","railf.jp","romet.pl","rukim.id","s.awa.fm","sbflix.*","senpa.io","sflix.ca","sflix.is","sflix.to","sj-r.com","tadu.com","talpo.it","tepat.id","tvn24.pl","ufret.jp","utour.me","vembed.*","vidsrc.*","virpe.cc","wtsp.com","xnxx.com","yuuki.me","zaui.com","zdnet.de","zgbk.com","1shows.ru","47news.jp","adpres.ro","ahzaa.net","aicesu.cn","anauk.net","aniwave.*","archon.gg","artsy.net","autodoc.*","b4usa.com","bmovies.*","brainly.*","brutal.io","cda-hd.cc","cpuid.com","critic.de","ctrl.blog","d000d.com","d0o0d.com","deepl.com","digi24.ro","do0od.com","do7go.com","doply.net","dramaqu.*","earth.com","eater.com","edurev.in","felico.pl","filhub.gr","fin24.com","flagle.io","fmovies.*","fotor.com","freep.com","globo.com","gmx.co.uk","hdrez.com","hianime.*","ibomma.pw","imooc.com","invado.pl","jootc.com","juejin.cn","keybr.com","lesoir.be","lexlog.pl","lohud.com","lublin.eu","lunas.pro","m4uhd.net","mangaku.*","matzoo.pl","mcloud.to","mm9841.cc","mocah.org","naver.com","nebula.tv","news24.jp","newsme.gr","ntvs.cx>>","ocala.com","ophim.vip","orange.ro","peekme.cc","player.pl","pling.com","quora.com","redisex.*","ruwix.com","s0urce.io","scmp3.org","seexh.com","sflix2.to","shein.com","sopot.net","tbs.co.jp","tides.net","tiempo.hn","tomshw.it","turbo1.co","txori.com","uemeds.cn","uihtm.com","umk.co.jp","uplod.net","veblr.com","velicu.eu","venea.net","vezess.hu","vide0.net","vidplay.*","vinaurl.*","virpe.com","watson.ch","watson.de","weibo.com","wired.com","women.com","world4.eu","wstream.*","x-link.pl","x-news.pl","xhbig.com","yeane.org","ytv.co.jp","yuque.com","zefoy.com","zgywyd.cn","zhihu.com","ziare.com","360doc.com","3xyaoi.com","4media.com","52bdys.com","699pic.com","actvid.com","adslink.pw","all3do.com","allsmo.com","analizy.pl","ananweb.jp","ancient.eu","animedao.*","auto-doc.*","bdb.com.pl","bejson.com","bembed.net","bestcam.tv","boards.net","boston.com","bpcj.or.jp","broflix.cc","caller.com","camcaps.to","chillx.top","citroen.pl","clujust.ro","crewus.net","crichype.*","curbed.com","d0000d.com","debeste.de","deezer.com","dejure.org","depedlps.*","dlions.pro","dlnews.com","drkrok.com","dxmaps.com","e-sushi.fr","earnload.*","ebc.com.br","embedv.net","esaral.com","fauxid.com","fflogs.com","filefox.cc","filiser.eu","film4e.com","fjordd.com","fnbrjp.com","foodie.com","fullxh.com","galinos.gr","gaz.com.br","ggwash.org","goerie.com","gomovies.*","gplinks.co","grunge.com","hdtoday.so","hienzo.com","hindipix.*","hitcena.pl","hoca4u.com","img999.com","ing-sat.hu","javbix.com","jdnews.com","jeu2048.fr","jeyran.net","jnews5.com","kapiert.de","knshow.com","lcpdfr.com","ldnews.com","legacy.com","listatv.pl","lofter.com","looper.com","love4u.net","lwlies.com","mashed.com","masuit.com","maxroll.gg","mbalib.com","mdlinx.com","medium.com","megaxh.com","menrec.com","milfzr.com","mongri.net","motogon.ru","mpnnow.com","naaree.com","neobux.com","neowin.net","newspao.gr","njjzxl.net","nny360.com","nypost.com","opedge.com","oploverz.*","pc3mag.com","peugeot.pl","piklodz.pl","pixnet.net","pixwox.com","pjstar.com","pokeos.com","polyvsp.ru","protest.eu","qidian.com","quotev.com","racked.com","rdsong.com","riwyat.com","rrstar.com","salina.com","sbenny.com","sbface.com","scribd.com","sdewery.me","sexpox.com","skuola.net","tcpalm.com","texte.work","tiktok.com","tmnews.com","top1iq.com","totemat.pl","tumblr.com","tvzingvn.*","uol.com.br","utamap.com","vcstar.com","vidply.com","vvide0.com","wader.toys","watchx.top","wormate.io","wpchen.net","xhamster.*","xhopen.com","xhspot.com","yamibo.com","youmath.it","zalukaj.io","zingtvhd.*","zingvntv.*","zulily.com","102bank.com","123movies.*","9xbuddy.com","abstream.to","accgroup.vn","adevarul.ro","affbank.com","amlesson.ru","anikaitv.to","aniwatch.to","antena3.com","aoezone.net","arcanum.com","asia2tv.com","ask4movie.*","autodoc24.*","badayak.com","bdcraft.net","bg-gledai.*","bhaskar.com","bianity.net","bimiacg.net","bitcine.app","bluphim.com","boke112.com","bypass.city","canale.live","cattime.com","cepuluh.com","civitai.com","civitai.red","clockks.com","cmjornal.pt","cnblogs.com","coinurl.net","comikey.com","cookhero.gr","d4armory.io","day-hoc.org","decider.com","disheye.com","djelfa.info","dogtime.com","dramacute.*","ds2play.com","duracell.de","elahmad.com","embasic.pro","embtaku.pro","eoreuni.com","epitesti.ro","esologs.com","esscctv.com","europixhd.*","explore.com","ezmanga.net","f2movies.ru","faptiti.com","flixrave.to","fosshub.com","fosters.com","fruit01.xyz","funivie.org","gamegame.kr","geotips.net","goalup.live","goodhub.xyz","hianimez.to","hidemywp.co","hongxiu.com","hotleak.vip","hotleaks.tv","howjsay.com","hoyolab.com","htrnews.com","hukmatpro.*","hulnews.top","ideapod.com","ilife97.com","infokik.com","inverse.com","jafekri.com","javbest.xyz","javgrab.com","jio.pftv.ws","kinston.com","kitguru.net","koltry.life","kpopsea.com","ktm2day.com","l2gamers.cl","lalawin.com","lasexta.com","lataifas.ro","leetcode.cn","logonews.cn","lolle21.com","lover93.net","maduras.vip","magesy.blog","malekal.com","mangatoon.*","manhwa18.cc","masrawy.com","maxt.church","mediafax.ro","milenio.com","mobiflip.de","moviepl.xyz","mrbenne.com","nettv4u.com","newsbook.pl","ngelmat.net","novelism.jp","novelza.com","ntuplay.xyz","ntvspor.net","nulled.life","nytimes.com","odiario.com","ohli365.vip","ohmygirl.ml","olarila.com","ontools.net","oreilly.com","otakudesu.*","pagesix.com","pancreas.ro","pandurul.ro","pashplus.jp","phimfit.com","pinterest.*","pngitem.com","poipiku.com","poli-vsp.ru","polygon.com","postype.com","promotor.pl","putlocker.*","qrcode.best","racevpn.com","radioony.fm","redding.com","romviet.com","rubystm.com","rubyvid.com","runmods.com","safetxt.net","satcesc.com","sbbrisk.com","sctimes.com","shaamtv.com","sherdog.com","shinbhu.net","shinchu.net","smalley.com","spectank.jp","starbene.it","stbnetu.xyz","strcloud.in","swtimes.com","taxo-acc.pl","teachoo.com","techgyd.com","tekstowo.pl","thelist.com","thotsbay.tv","tinyppt.com","tistory.com","titulky.com","topfaps.com","trakteer.id","trentino.pl","tuborstb.co","tunegate.me","turbolab.it","tv.bdix.app","tvn24bis.pl","tvnstyle.pl","tvnturbo.pl","twitter.com","unixhow.com","untitle.org","upstream.to","uta-net.com","uticaod.com","v6embed.xyz","vedantu.com","veneto.info","vgembed.com","vidembed.me","videovard.*","viewing.nyc","voirfilms.*","wattpad.com","wawlist.com","wikihow.com","winaero.com","winmeen.com","wired.co.uk","wishflix.cc","wizcase.com","xhamster1.*","xhamster2.*","xhamster3.*","xhamster4.*","xhamster5.*","xhamster7.*","xhamster8.*","xhmoon5.com","xhreal2.com","xhtotal.com","xhwide5.com","xossipy.com","ymovies.vip","zerogpt.net","ziperto.com","zonatmo.com","30edu.com.cn","4x4earth.com","abril.com.br","abysscdn.com","adbypass.org","afrikmag.com","agrointel.ro","allmovie.com","amarillo.com","amestrib.com","amtraker.com","anikototv.to","anime2you.de","anisearch.de","anisubindo.*","athletic.net","autoembed.cc","avdelphi.com","bigulnews.tv","bilibili.com","bitblokes.de","bonobono.com","bphimmoi.net","ciweimao.com","cjonline.com","codedosa.com","cool-etv.net","crewbase.net","cronista.com","descopera.ro","dispatch.com","dollarvr.com","doodstream.*","ds2video.com","dushu.qq.com","einthusan.tv","elektroda.pl","elheraldo.hn","enternity.gr","fabricjs.com","fairyabc.com","fightful.com","filmzone.com","foodviva.com","forplayx.ink","fosspost.org","fpmmusic.com","fxstreet.com","gamerant.com","gardenia.net","gay69.stream","gdplayertv.*","gearside.com","geniusjw.com","ggeguide.com","ggulpass.com","globaledu.jp","gmbinder.com","gnt24365.net","habuteru.com","hindi-gk.com","ieltsliz.com","ikorektor.pl","indystar.com","inquirer.net","intramed.net","itvnextra.pl","javjavhd.com","jbjbgame.com","jconline.com","jobskaro.com","joysound.com","jsonline.com","kaystls.site","kentucky.com","knoxnews.com","kolnovel.com","korona.co.jp","kritichno.bg","kurazone.net","kurosave.com","kusonime.com","lazyadmin.nl","leekduck.com","lifestory.hu","ligowiec.net","linkmate.xyz","liverpool.no","lookmovie.ag","lookmovie2.*","lowcygier.pl","mangainn.net","megacloud.tv","megapixl.com","megatube.xxx","meteo.org.pl","mimikama.org","mineskin.org","mmamania.com","moneyguru.co","movieweb.com","msubplix.com","myflixerz.to","myoplay.club","napiszar.com","njherald.com","nonton78.com","novagente.pt","novelpia.com","nowcoder.com","npnews24.com","nsfwzone.xyz","nwherald.com","nzbstars.com","olacast.live","omnisets.com","oricon.co.jp","otakukan.com","ouasafat.com","pal-item.com","palemoon.org","paxdei.th.gl","pcpobierz.pl","pelispedia.*","pentruea.com","photopea.com","picallow.com","pitesti24.ro","playbill.com","playmogo.com","pornhd8k.net","portalwrc.pl","powerline.io","priberam.org","pupupul.site","putlocker.pe","radarbox.com","radichubu.jp","redecanais.*","reflectim.fr","relet365.com","revenue.land","sarthaks.com","sbnation.com","shumilou.com","sidereel.com","solarmovie.*","sportnews.to","sportsnet.ca","steptalk.org","streamsb.net","streamtape.*","sussytoons.*","suzylu.co.uk","techsini.com","tecmundo.net","telegram.com","th-world.com","theblaze.com","thegamer.com","theverge.com","thizissam.in","topeuropix.*","transinfo.pl","tritinia.com","tutlehd4.com","tvnfabula.pl","tvtropes.org","ultraten.net","unidivers.fr","urbharat.xyz","usatoday.com","valuexh.life","vid2faf.site","vidplay.site","vidtube.site","visse.com.br","voeunblk.com","volokit2.com","webnovel.com","webwereld.nl","wrosinski.pl","wzamrani.com","xclient.info","xhaccess.com","xhadult4.com","xhamster10.*","xhamster11.*","xhamster12.*","xhamster13.*","xhamster14.*","xhamster15.*","xhamster16.*","xhamster17.*","xhamster18.*","xhamster19.*","xhamster20.*","xhamster42.*","xhamster46.*","xhdate.world","yhocdata.com","0123movies.ch","4kwebplay.xyz","7misr4day.com","adslayuda.com","aha-music.com","alfred.camera","animedrive.hu","animeunity.it","anisearch.com","aniwatchtv.to","ark-unity.com","artesacro.org","asheville.com","audiotools.in","autophorie.de","azcentral.com","aztravels.net","blindhelp.net","blog.csdn.net","blog.kwick.de","bluesnews.com","bongdaplus.vn","box-manga.com","bricksrus.com","broncoshq.com","buienradar.nl","cantonrep.com","casertace.net","centrumher.eu","chieftain.com","chowhound.com","city-data.com","cocomanga.com","coffeeapps.ir","colourxh.site","cyberalert.gr","dailymail.com","dddance.party","desertsun.com","desijugar.net","deutschaj.com","dlmovies.link","dooodster.com","downfile.site","eca-anime.net","economica.net","emailfake.com","eplayer.click","fantricks.com","firescans.xyz","firestream.to","flory4all.com","flyertalk.com","fontsfree.pro","foxaholic.com","foxteller.com","fraudnavi.com","full-anime.fr","galesburg.com","gaminplay.com","getective.com","gezimanya.com","gmarket.co.kr","goodbakery.ru","goupstate.com","gukjenews.com","helldivers.io","hellokpop.com","hillsdale.net","holakikou.com","howtogeek.com","hutchnews.com","icy-veins.com","ideas0419.com","infodifesa.it","instagram.com","iptv4best.com","jk-market.com","kapitalis.com","kitsapsun.com","kpopjjang.com","laptopmag.com","leeyiding.com","libertatea.ro","limametti.com","listeamed.net","live.b-c-e.us","liveonsat.com","livetennis.it","longecity.org","loverslab.com","m.youtube.com","makeuseof.com","mangaid.click","maxedtech.com","mediafire.com","mediotejo.net","megaplay.buzz","megawypas.com","memangbau.com","meteoblue.com","mocospace.com","movie-web.app","movie4kto.net","mt07-forum.de","mzzcloud.life","nbcsports.com","neilpatel.com","neoseeker.com","newbernsj.com","newportri.com","newschief.com","newyorker.com","neyrologos.gr","nicematin.com","oakridger.com","oceanplay.org","oklahoman.com","otakudesu.org","otempo.com.br","perplexity.ai","phrasemix.com","piecesauto.fr","plural.jor.br","polsatnews.pl","polyflore.net","proboards.com","protopage.com","putlocker.vip","qqwebplay.xyz","radartest.com","radio5.com.pl","readnovel.com","recordnet.com","routenote.com","sachonthi.com","sat-charts.eu","savvytime.com","scrolller.com","sh.reddit.com","shopomo.co.uk","shortform.com","slashfilm.com","slashgear.com","solotrend.net","southcloud.tv","spookshow.net","sportsupa.com","sporttotal.tv","statesman.com","store.kde.org","streamvid.net","studyadda.com","suedkurier.de","swtorlogs.com","t.17track.net","techkings.org","temperatur.nu","theintell.com","theledger.com","thememypc.net","thethings.com","thewpclub.net","tiermaker.com","timponline.ro","tomsguide.com","top.howfn.com","torontosom.ca","trangchu.news","trojmiasto.pl","tweaktown.com","ubuntudde.com","unikampus.net","uniqueten.net","unlockxh4.com","up4stream.com","uwayapply.com","vid-guard.com","videohelp.com","vidstream.pro","vipstreams.in","visionias.net","vnexpress.net","voe-unblock.*","voeunblck.com","vpnmentor.com","vtube.network","warning.or.kr","waves4you.com","wikibious.com","www.ntv.co.jp","xfce-look.org","xhbranch5.com","xhchannel.com","xhplanet1.com","xhplanet2.com","xhvictory.com","xiaomi4mi.com","yoyofilmeys.*","zerohedge.com","zwei-euro.com","99bitcoins.com","adnan-tech.com","ajanstv.com.tr","allcryptoz.net","ananda-yoga.ro","androidmtk.com","anime-drama.jp","animefire.plus","arlinadzgn.com","audiostereo.pl","auto-treff.com","autopareri.com","battle-one.com","bharatavani.in","bigdatauni.com","bikesell.co.kr","bingotingo.com","blog.naver.com","brownsboys.com","btvnovinite.bg","cafe.naver.com","cdramalove.com","chronologia.pl","cincinnati.com","clasicotas.org","clipartmax.com","coinsparty.com","coloradoan.com","comingsoon.net","crunchyscan.fr","curseforge.com","daily-jeff.com","dailycomet.com","dailyworld.com","daotranslate.*","dba-oracle.com","demolandia.net","developpez.com","diaforetiko.gr","doc.mbalib.com","dodge-forum.eu","dreamstime.com","droidtekno.com","dzwignice.info","edailybuzz.com","emturbovid.com","enduro-mtb.com","erinsakura.com","estadao.com.br","eveningsun.com","evreporter.com","fimfiction.net","freeforums.net","fucktube4k.com","funnyordie.com","galleryxh.site","gamebanana.com","genesistls.com","gnome-look.org","golfdigest.com","guiasaude.info","heraldnews.com","houmatoday.com","how-to-pc.info","icourse163.org","ideaberita.com","impots.gouv.fr","indeonline.com","indiatimes.com","infoplease.com","intergate.info","iphonecake.com","iwanichi.co.jp","jacksonsun.com","japan-fans.com","javsubtitle.co","jeniusplay.com","jpopsingles.eu","kangmartho.com","karsaz-law.com","katosatoshi.jp","kicknews.today","kuchniaplus.pl","kutub3lpdf.com","lcsun-news.com","leakedzone.com","learninsta.com","lenconnect.com","lendagames.com","linux-apps.com","lowkeytech.com","mail.yahoo.com","majorgeeks.com","malybelgrad.pl","mangareader.to","mangaschan.net","marionstar.com","mindmegette.hu","mixmods.com.br","mixstreams.top","mkv-pastes.com","moegirl.org.cn","moneyexcel.com","monroenews.com","moviesapi.club","movingxh.world","musicradar.com","musixmatch.com","myhtebooks.com","naijagists.com","naplesnews.com","naukridisha.in","ndtvprofit.com","nekopoi.web.id","netuplayer.top","news-press.com","news.17173.com","news.dwango.jp","news.ntv.co.jp","newsherald.com","newsleader.com","nickiswift.com","nogizaka46.com","ofuxico.com.br","oggiscuola.com","one.oregon.gov","oparana.com.br","openfinanza.it","otvfoco.com.br","paidiatreio.gr","payeer-gift.ru","pecasauto24.pt","pekintimes.com","peliculas24.me","playerx.stream","prepostseo.com","pushsquare.com","rapid-cloud.co","readawrite.com","realpython.com","redecanaistv.*","remixsearch.es","reviewmeta.com","riftherald.com","rightnonel.com","rivestream.org","rozbor-dila.cz","runningnews.gr","screenrant.com","scsun-news.com","selfstudys.com","seriesperu.com","shelbystar.com","shrinkearn.com","slideshare.net","sokolow-mlp.pl","starzunion.com","szkolawohyn.pl","techjunkie.com","techus.website","tekloggers.com","tennessean.com","the-leader.com","the-review.com","theflixertv.to","thegleaner.com","thehawkeye.com","themebanks.com","thestar.com.my","thezealots.org","timeanddate.de","timeanddate.no","topautoosat.fi","topcryptoz.net","translate.goog","tv-asahi.co.jp","tv-tokyo.co.jp","tv.youtube.com","tvfreemium.top","tvstreampf.xyz","urbanbrush.net","verselemzes.hu","voeunbl0ck.com","wasza-farma.pl","webcamtaxi.com","whatfontis.com","wheel-size.com","whoisnovel.com","world-novel.fr","wpplugins.tips","www.reddit.com","xhofficial.com","xhwebsite5.com","zipcode.com.ng","10000recipe.com","aepos.ap.gov.in","airfrance.co.jp","airnavradar.com","all4pets.com.pl","alltechnerd.com","altranotizia.it","androidtvbox.eu","appimagehub.com","appofmirror.com","arcanescans.com","argusleader.com","atribuna.com.br","auth.alipay.com","awebstories.com","bestjavporn.com","blitzrechner.de","bluemediafile.*","books-world.net","bucketpages.com","c4ddownload.com","calorielijst.nl","cinegrabber.com","cinemablend.com","comprerural.com","cristoiublog.ro","cssreference.io","cypherscans.xyz","daily-times.com","dailymail.co.uk","dailyrecord.com","delmarvanow.com","desbloqueador.*","diffchecker.com","drawasaurus.org","dubznetwork.com","dztechphone.com","elektrikmen.com","elitepvpers.com","elpasotimes.com","fabioambrosi.it","famousintel.com","fayobserver.com","fcportables.com","fdlreporter.com","flinsetyadi.com","formatatmak.com","freewatchtv.top","futbollatam.com","gagetmatome.com","gainesville.com","glistranieri.it","gosanangelo.com","guitarworld.com","halotracker.com","hansa-online.de","heavyfetish.com","hentaihaven.xxx","hibiki-radio.jp","hotpornfile.org","housedigest.com","ihbarweb.org.tr","ilsole24ore.com","includehelp.com","indahonline.com","japonhentai.com","kanjukulive.com","katerionews.com","kickante.com.br","kooora4livs.com","koszalincity.pl","langitmovie.com","lethalpanda.com","lgbtqnation.com","licensekeys.org","linuxslaves.com","livescience.com","loginhit.com.ng","loudersound.com","loveplay123.com","manhwahentai.me","maxstream.video","medeberiya.site","mediahiburan.my","mehoathinh2.com","miniminiplus.pl","mmafighting.com","moneydigest.com","movies2watch.ru","music.apple.com","news-leader.com","news.chosun.com","northjersey.com","noweconomy.live","onlinetools.com","opendesktop.org","order-order.com","pawastreams.pro","pendulumedu.com","pepperlive.info","phimdinhcao.com","piecesauto24.lu","playonlinux.com","pogdesign.co.uk","polagriparts.pl","poolpiscina.com","primicia.com.ve","privivkainfo.ru","promobit.com.br","prpm.dbp.gov.my","putlockernew.vc","qiangwaikan.com","quicksleeper.pl","randomstory.org","read.amazon.com","reborntrans.com","romprovider.com","ruidosonews.com","saikaiscans.net","savannahnow.com","sekaikomik.live","short-story.net","smashboards.com","sneakernews.com","spanishdict.com","starcourier.com","stargazette.com","statelibrary.us","staugustine.com","stream.bunkr.is","tallahassee.com","targetstudy.com","team-octavi.com","techlicious.com","technicpack.net","teile-direkt.ch","textcleaner.net","thegearhunt.com","thememazing.com","thenekodark.com","thenewsstar.com","thespectrum.com","thetowntalk.com","timeanddate.com","timesonline.com","tvshowstars.com","twinkietown.com","ukrainashop.com","uslsoftware.com","venusembed.site","videobot.stream","voe-unblock.com","voeun-block.net","voeunblock3.com","wallauonline.de","wenku.baidu.com","wrestlezone.com","www.youtube.com","yeuphimmoik.com","youtubekids.com","zippyupload.com","zoommastory.com","aberdeennews.com","acupoffrench.com","addons.opera.com","airlinercafe.com","alphapolis.co.jp","animecruzers.com","apornstories.com","arenavalceana.ro","articlesmania.me","as-selection.net","blueridgenow.com","book.zhulang.com","booksmedicos.org","bumigemilang.com","cabinetexpert.ro","canondrivers.org","capecodtimes.com","carsguide.com.au","cdnmoviking.tech","celebzcircle.com","celtadigital.com","cittadinanza.biz","civildigital.com","cleanthinking.de","commandlinux.com","courierpress.com","creativebloq.com","currentargus.com","cyberspace.world","dailynews.us.com","daya-jewelry.com","deccanherald.com","dicasdevalor.net","digminecraft.com","dongphimmoiz.com","dreamsfriend.com","dualshockers.com","easyayurveda.com","englishlands.net","erovideoseek.com","eurooptyk.com.pl","experciencia.com","felizemforma.com","firmwarefile.com","floridatoday.com","fmhikayeleri.com","foodrepublic.com","freetvsports.xyz","freewaysintl.com","fv2freegifts.org","gadsdentimes.com","gordiando.com.br","grandoldteam.com","hardcoregames.ca","healthdigest.com","hoosiertimes.com","htmlreference.io","husseinezzat.com","ilovevaldinon.it","info-beihilfe.de","infomoney.com.br","interviewgig.com","isekaipalace.com","iskandinavya.com","itscybertech.com","jacksonville.com","jamilacuisine.ro","jusbrasil.com.br","justswallows.net","kamerabudaya.com","karyawanesia.com","kitchennovel.com","klsescreener.com","knowyourmeme.com","kollyinsider.com","kooora4lives.net","lokercirebon.com","madeinbocholt.de","medievalists.net","metropoliaztm.pl","milesofmusik.com","money-sense.club","myschool-eng.com","ncrtsolutions.in","newsforbolly.org","nhentaihaven.org","nofilmschool.com","nonesnanking.com","numberempire.com","nusantararom.org","nwfdailynews.com","nydailyquote.com","ofertecatalog.ro","onlineathens.com","outdoorguide.com","outidesigoto.com","paesifantasma.it","perlentaucher.de","petoskeynews.com","poconorecord.com","polskacanada.com","ponselharian.com","popcornmovies.io","portableapps.com","postcrescent.com","pttws.ptt.gov.tr","pureinfotech.com","rabbitstream.net","rapidairmax.site","raven-mythic.com","recordonline.com","repack-games.com","reporternews.com","reservdelar24.se","resourcepack.net","ribbelmonster.de","rule34hentai.net","sabishiidesu.com","savoriurbane.com","script-stack.com","segnidalcielo.it","sekai-kabuka.com","seoul.cs.land.to","sertracen.com.pa","simpleflying.com","sinhasannews.com","skidrowcodex.net","smokelearned.net","socialcounts.org","solarmagazine.nl","songs-wayaku.com","sssscanlator.com","ssuathletics.com","straitstimes.com","studiestoday.com","studyrankers.com","sweetslyrics.com","tabonitobrasil.*","tastingtable.com","tech-recipes.com","techtrickseo.com","tecnotutoshd.net","telefon-treff.de","tercihiniyap.net","thailandopen.org","the-dispatch.com","thedailymeal.com","thestarpress.com","thetimesnews.com","todaysparent.com","tohkaishimpo.com","tools.jabrek.net","tweaking4all.com","twitchemotes.com","ukworkshop.co.uk","un-block-voe.net","unknowncheats.me","vidstreaming.xyz","viewsofgreece.gr","vinstartheme.com","visefierbinti.ro","voe-un-block.com","voxvalachorum.ro","vvdailypress.com","wallpapercat.com","warcraftlogs.com","web.facebook.com","webcodegeeks.com","wikiofcelebs.com","wildstarlogs.com","willow.arlen.icu","wouterplanet.com","wrestlinginc.com","www.facebook.com","zdravenportal.eu","ziarulargesul.ro","zsti.zsti.civ.pl","affiliate.fc2.com","androidmakale.com","androidpolice.com","androidweblog.com","answersafrica.com","arras.netlify.app","balticlivecam.com","banglainsider.com","beaconjournal.com","blueraindrops.com","book.zongheng.com","braziljournal.com","brooklyneagle.com","cagesideseats.com","charbelnemnom.com","cheboygannews.com","chessimprover.com","chimica-online.it","cinemakottaga.top","citizen-times.com","citpekalongan.com","claplivehdplay.ru","clarionledger.com","classnotes.org.in","coolwallpapers.me","counciloflove.com","daily-tohoku.news","dailyamerican.com","dailynewsview.com","daimangajiten.com","dassen-azara4.com","daysoftheyear.com","deportealdia.live","der-postillon.com","descarga-animex.*","digitaltrends.com","encurtandourl.com","enjoytaiwan.co.kr","fordogtrainers.pl","francis-bacon.com","gamingsinners.com","gastongazette.com","geeksforgeeks.org","geeksoncoffee.com","good-football.org","googleapis.com.de","googleapis.com.do","gq-magazine.co.uk","grostembed.online","guides4gamers.com","heraldtribune.com","heypoorplayer.com","hitproversion.com","hollywoodmask.com","insidermonkey.com","ithacajournal.com","janvissersweer.nl","japanxxxmovie.com","jobsbotswana.info","jornaljoca.com.br","justtrucks.com.au","katholisches.info","kursnacukrzyce.pl","labs.j-novel.club","langweiledich.net","letsdownloads.com","lewblivehdplay.ru","liveyourmaths.com","lubbockonline.com","lugarcerto.com.br","luoghidavedere.it","manianomikata.com","marinetraffic.com","mcocguideblog.com","mcskinhistory.com","media.framu.world","memoryhackers.org","molineuxmix.co.uk","mooc.chaoxing.com","mtbtutoriales.com","music.youtube.com","nbcsportsedge.com","neuroteam-metz.de","nfltraderumors.co","nordkorea-info.de","nostracasa.com.br","oceanof-games.com","palmbeachpost.com","patriotledger.com","phimlongtieng.net","press-citizen.com","pressconnects.com","progameguides.com","recambioscoche.es","registerguard.com","reportergazeta.pl","roztoczanskipn.pl","scarysymptoms.com","serwis-zamkow.com","sharktankblog.com","sizyreelingly.com","sklep-agroland.pl","soundcloudmp3.org","starsunfolded.com","tchadcarriere.com","terramirabilis.ro","the-scorpions.com","theadvertiser.com","theaircurrent.com","theepochtimes.com","thegraillords.net","theregister.co.uk","times-gazette.com","timesreporter.com","timestelegram.com","toppremiumpro.com","torrentlawyer.com","urochsunloath.com","v-o-e-unblock.com","valeronevijao.com","venusarchives.com","verpornocomic.com","visaonoticias.com","watch.lonelil.com","winhelponline.com","wolfdyslectic.com","workhouses.org.uk","yaledailynews.com","alamogordonews.com","asianexpress.co.uk","autoteiledirekt.de","badgerandblade.com","baixedetudo.net.br","besteonderdelen.nl","bloomberglinea.com","bloombergquint.com","boerse-express.com","bronze-bravery.com","coffeeforums.co.uk","cografyahocasi.com","cours-de-droit.net","craftpip.github.io","delawareonline.com","doranobi-fansub.id","eduardo-monica.com","endorfinese.com.br","enterprisenews.com","esercizinglese.com","evasion-online.com","eveningtribune.com","fantasytagtree.com","ferroviando.com.br","figeterpiazine.com","financasdeouro.com","flashdumpfiles.com","flashplayer.org.ua","followmikewynn.com","foreignaffairs.com","freesmsgateway.com","gaypornmasters.com","giromarilia.com.br","gossipnextdoor.com","hayatbilgileri.com","heroesneverdie.com","immobiliaremia.com","iovivoatenerife.it","keighleynews.co.uk","kijyomatome-ch.com","krunkercentral.com","kuroko-analyze.com","lincolncourier.com","luyenthithukhoa.vn","mcdonoughvoice.com","mesquitaonline.com","minecraftforge.net","motortrader.com.my","myfreemp3juices.cc","nationalreview.com","newarkadvocate.com","onlinegiftools.com","onlinejpgtools.com","onlinepngtools.com","onscreensvideo.com","openanesthesia.org","placementstore.com","planetagibi.com.br","pokemonforever.com","portalportuario.cl","postcourier.com.pg","progress-index.com","psihologiadeazi.ro","record-courier.com","renditepassive.net","reporter-times.com","rezervesdalas24.lv","rottentomatoes.com","samsungtechwin.com","sdelatotoplenie.ru","seacoastonline.com","serieslyawesome.tv","sheboyganpress.com","skandynawiainfo.pl","sooeveningnews.com","sovetromantica.com","space-engineers.de","starnewsonline.com","steamcollector.com","stiridinromania.ro","strangermeetup.com","sturgisjournal.com","tauntongazette.com","techsupportall.com","theasianparent.com","thecalifornian.com","thegardnernews.com","theherald-news.com","theitaliantimes.it","thejakartapost.com","themosvagas.com.br","thetimesherald.com","thinkamericana.com","titanic-magazin.de","topperlearning.com","truyenbanquyen.com","tuscaloosanews.com","unlimitedfiles.xyz","upsrtconline.co.in","vercalendario.info","verdadeiroolhar.pt","viveretenerife.com","wirtualnyspac3r.pl","wpb.shueisha.co.jp","xda-developers.com","xxxonlinegames.com","yodelswartlike.com","aileen-novel.online","atlas-geografic.net","bluemoon-mcfc.co.uk","columbiatribune.com","courier-journal.com","courier-tribune.com","csiplearninghub.com","dailycommercial.com","darktranslation.com","demingheadlight.com","descargatepelis.com","dialectsarchive.com","dicasdefinancas.net","digitalfernsehen.de","digitalsynopsis.com","download.ipeenk.com","dreamlandresort.com","duneawakening.th.gl","empregoestagios.com","exclusifvoyages.com","festival-cannes.com","frameboxxindore.com","gazetadopovo.com.br","generationamiga.com","goodnews-magazin.de","handball-world.news","harvardmagazine.com","heraldmailmedia.com","hollandsentinel.com","home.novel-gate.com","independentmail.com","investorvillage.com","jacquieetmichel.net","journalstandard.com","kashmirobserver.net","kirannewsagency.com","legionprogramas.org","livingstondaily.com","lyricstranslate.com","marksandspencer.com","mexiconewsdaily.com","morosedog.gitlab.io","mostrodifirenze.com","musicallyvideos.com","mycentraljersey.com","mzk.starachowice.eu","nakedcapitalism.com","ncert-solutions.com","ncertsolutions.guru","norwichbulletin.com","onlinecoursebay.com","onlinetexttools.com","opportunitydesk.org","orangespotlight.com","perangkatguruku.com","raccontivietati.com","raindropteamfan.com","samurai.wordoco.com","seikatsu-hyakka.com","selfstudyanthro.com","shreveporttimes.com","siliconinvestor.com","smartkhabrinews.com","southcoasttoday.com","starresonance.th.gl","thedailyjournal.com","thedraftnetwork.com","thenorthwestern.com","theonegenerator.com","therecordherald.com","timesrecordnews.com","tipssehatcantik.com","tuttoautoricambi.it","viatasisanatate.com","wallpaperaccess.com","worldscientific.com","aboutchromebooks.com","alphagirlreviews.com","animenewsnetwork.com","astro-cric.pages.dev","augustachronicle.com","autoalkatreszek24.hu","autodielyonline24.sk","badzjeszczelepszy.pl","cdn.gamemonetize.com","cissamagazine.com.br","clubulbebelusilor.ro","commercialappeal.com","compartiendofull.net","corriereadriatico.it","coshoctontribune.com","cristelageorgescu.ro","criticalthinking.org","elektro-plast.com.pl","freereadnovel.online","greenvilleonline.com","hedgeaccordingly.com","ifdreamscametrue.com","impotsurlerevenu.org","karamellstore.com.br","koalasplayground.com","lazytranslations.com","lesmoutonsenrages.fr","magesyrevolution.com","mainframegurukul.com","marriedbiography.com","metagnathtuggers.com","milforddailynews.com","odiarioonline.com.br","onlinecarparts.co.uk","onlinefreecourse.net","photoshop-online.biz","platform.twitter.com","psychologiazycia.com","punto-informatico.it","readcomicsonline.lol","reservedeler24.co.no","revistavanityfair.es","selfstudyhistory.com","shushan.zhangyue.net","southbendtribune.com","statesmanjournal.com","stockpokeronline.com","technologyreview.com","tempatwisataseru.com","the-daily-record.com","theartofnakedwoman.*","thedailyreporter.com","thegatewaypundit.com","theleafchronicle.com","themeparktourist.com","thepublicopinion.com","ultimate-bravery.net","viafarmaciaonline.it","vinaurl.blogspot.com","windows101tricks.com","aprendeinglessila.com","autoczescionline24.pl","bibliacatolica.com.br","blasianluvforever.com","blogvisaodemercado.pt","bloomberglinea.com.br","cantondailyledger.com","columbiaspectator.com","courierpostonline.com","delicateseliterare.ro","desmoinesregister.com","devilslakejournal.com","diariodoiguacu.com.br","digital.lasegunda.com","download.mokeedev.com","downloadtutorials.net","ellwoodcityledger.com","filmpornoitaliano.org","gamoneinterrupted.com","glamourmagazine.co.uk","globaldefensecorp.com","goldenstateofmind.com","granfondo-cycling.com","greatfallstribune.com","guidingliterature.com","hearthstone-decks.net","hebrew4christians.com","ilclubdellericette.it","ilovefreesoftware.com","ipphone-warehouse.com","japancamerahunter.com","juancarlosmolinos.net","links.extralinks.casa","northwestfirearms.com","onlinestringtools.com","pcso-lottoresults.com","practicetestgeeks.com","premiumembeding.cloud","programming-link.info","promotor-poz.kylos.pl","providencejournal.com","searchenginewatch.com","smokingmeatforums.com","streamservicehd.click","the-masters-voice.com","thenews-messenger.com","tinyhouse-baluchon.fr","uptimeside.webnode.gr","visaliatimesdelta.com","wausaudailyherald.com","cathouseonthekings.com","chillicothegazette.com","cyberkrafttraining.com","dicasfinanceirasbr.com","digitalcameraworld.com","elizabeth-mitchell.org","generatesnitrosate.com","hiraethtranslation.com","hitokageproduction.com","japan-academy-prize.jp","kulinarnastronamocy.pl","labreakfastburrito.com","mainframestechhelp.com","metrowestdailynews.com","monorhinouscassaba.com","mt-milcom.blogspot.com","musicindustryhowto.com","nationalgeographic.com","news-journalonline.com","notificationsounds.com","operatorsekolahdbn.com","palmbeachdailynews.com","planetagibiblog.com.br","pontiacdailyleader.com","qualityfilehosting.com","techieway.blogspot.com","telyn610zoanthropy.com","thehouseofportable.com","tutoganga.blogspot.com","unbiasedsenseevent.com","underconsideration.com","wiibackupmanager.co.uk","zeeebatch.blogspot.com","battlecreekenquirer.com","burlingtonfreepress.com","columbiadailyherald.com","examiner-enterprise.com","farm-ro.desigusxpro.com","feel-the-darkness.rocks","greenocktelegraph.co.uk","guidon40hyporadius9.com","hattiesburgamerican.com","juegosdetiempolibre.org","lansingstatejournal.com","mercenaryenrollment.com","oferty.dsautomobiles.pl","onlineonderdelenshop.nl","poughkeepsiejournal.com","przegladpiaseczynski.pl","publicopiniononline.com","rationalityaloelike.com","recantodasletras.com.br","republicadecuritiba.net","ryuryuko.blog90.fc2.com","searchenginejournal.com","sqlserveregitimleri.com","stevenspointjournal.com","theghostinmymachine.com","usmleexperiences.review","ate60vs7zcjhsjo5qgv8.com","bendigoadvertiser.com.au","cloudcomputingtopics.net","colegiosconcertados.info","democratandchronicle.com","gamershit.altervista.org","greenbaypressgazette.com","hentaialtadefinizione.it","indianhealthyrecipes.com","mansfieldnewsjournal.com","marshfieldnewsherald.com","montgomeryadvertiser.com","my-code4you.blogspot.com","phenomenalityuniform.com","photobank.mainichi.co.jp","programasvirtualespc.net","stowarzyszenie-impuls.eu","timeshighereducation.com","tricountyindependent.com","warringtonguardian.co.uk","webnoveltranslations.com","antallaktikaexartimata.gr","audaciousdefaulthouse.com","bucyrustelegraphforum.com","burlingtoncountytimes.com","ciberduvidas.iscte-iul.pt","creative-chemistry.org.uk","cyamidpulverulence530.com","dicionariocriativo.com.br","docs.paloaltonetworks.com","greaseball6eventual20.com","kathleenmemberhistory.com","lancastereaglegazette.com","matriculant401merited.com","portalcriatividade.com.br","portclintonnewsherald.com","realfinanceblogcenter.com","telenovelas-turcas.com.es","worldpopulationreview.com","yusepjaelani.blogspot.com","30sensualizeexpression.com","boonlessbestselling244.com","businessemailetiquette.com","globalairportconcierge.com","interestingengineering.com","northumberland-walks.co.uk","secondlifetranslations.com","singingdalong.blogspot.com","wisconsinrapidstribune.com","69translations.blogspot.com","buckscountycouriertimes.com","colors.sonicthehedgehog.com","garyfeinbergphotography.com","streaminglearningcenter.com","wasserstoff-leitprojekte.de","zanesvilletimesrecorder.com","courseware.cemc.uwaterloo.ca","economictimes.indiatimes.com","mimaletamusical.blogspot.com","springfieldspringfield.co.uk","tnt2-cricstreaming.pages.dev","toxitabellaeatrebates306.com","wlo-cricstreamiing.pages.dev","www-daftarharga.blogspot.com","xn--90afacv0cu2a3cr.xn--p1ai","arti-definisi-pengertian.info","divineyogaschool.blogspot.com","fittingcentermondaysunday.com","launchreliantcleaverriver.com","nahrungsmittel-intoleranz.com","utorrentgamesps2.blogspot.com","zeustranslations.blogspot.com","20demidistance9elongations.com","projektowanie-wnetrz-online.pl","audioreview.m1001.coreserver.jp","freerapidleechlist.blogspot.com","observatoriodocinema.uol.com.br","poplinks.idolmaster-official.jp","xn--90afacv0clj6ac0dxa.xn--p1ai","insurance-corporate.blogspot.com","mimaletadepeliculas.blogspot.com","certificationexamanswers.890m.com","telecom.economictimes.indiatimes.com","librospreuniversitariospdf.blogspot.com","xn-----0b4asja7ccgu2b4b0gd0edbjm2jpa1b1e9zva7a0347s4da2797e8qri.xn--1ck2e1b"];
    const collectArglistRefIndices = (out, hn, r) => {
        let l = 0, i = 0, d = 0;
        let candidate = '';
        while ( l < r ) {
            i = l + r >>> 1;
            candidate = $scriptletHostnames$[i];
            d = hn.length - candidate.length;
            if ( d === 0 ) {
                if ( hn === candidate ) {
                    out.add(i); break;
                }
                d = hn < candidate ? -1 : 1;
            }
            if ( d < 0 ) {
                r = i;
            } else {
                l = i + 1;
            }
        }
        return i + 1;
    };
    const indicesFromHostname = (out, hnDetails, suffix = '') => {
        if ( hnDetails.hns.length === 0 ) { return; }
        let r = $scriptletHostnames$.length;
        for ( const hn of hnDetails.hns ) {
            r = collectArglistRefIndices(out, `${hn}${suffix}`, r);
        }
        if ( $hasEntities$ ) {
            let r = $scriptletHostnames$.length;
            for ( const en of hnDetails.ens ) {
                r = collectArglistRefIndices(out, `${en}${suffix}`, r);
            }
        }
    };
    const todoIndices = new Set();
    indicesFromHostname(todoIndices, entries[0]);
    if ( $hasAncestors$ ) {
        for ( const entry of entries ) {
            if ( entry.i === 0 ) { continue; }
            indicesFromHostname(todoIndices, entry, '>>');
        }
    }
    // Collect arglist references
    if ( todoIndices.size ) {
        const $scriptletArglistRefs$ = /* 2109 */ "768;397;714,715,716;6,49;681;35,115;613;26;772;120,152,154,214;285;115;43;35;212;368;35;783;389;6;445;445;35,36;14,16,590;561;546;667;22,63;761;232,233,234,246;398;620;736;236;390;775;14;43;667;35,115;720;89;170;333;9,31;721;445;145;30;387;423;306;689;22,42,43,59;667;30,171,172;667;191;821;445;773;357;35;198;14,16,590;667;546;511;240;505;814;745;745;35;43;807;42;43;35;6,25;42;14,19,754;35,115;202,207;288;35;714,715;659;42;35;259;35;204,744;20;546;187;427;169;92;441;30;55;430;519;25;9,31;251;465;184;688;688;687,688;667;461;70;442;445;35,503;537;207,208;202,207,212,232,756,757;35,56,545;741;352;267;3;376;6,258;232,233,234,235;26;41;14;355;527;714,715,716;764;1;801;303;509;649;711;214;522;470;356;35,115;35,115;42;42;35,115;35,115;35,115;26;488;357;26,42,149;6;4;342;273;6,9,69,715;399;667,721;42;170;43;212;26;595;153;10,24,43,497,498,499;121;429;396;14,15,16;667;35;55;449;26,35;25,35;715;6,139;25,610;765;790;35;6,8,48;30;667;186;260;596;445;725;559;748;366;237;276;728;688;804;460;502;267;9,31;341;35;184;621;35;89;55;138;6;426;810,811;35,115;716;90;14,56;268;268;243;560;42;43,79,549,550,551;27,30;445;445;728;6;14;42;152;6;153;42;14,593,594;6,30;35;27;533,592;77;23,30;35,115;542;513;35;304;162;801;547;263;207,208;169;1;721;6;169;667;164;162;35,562;6,8,66;23,35;783;357;35,115;25;296,466;819;6;204;3;9,31;459;14,49;390;300;207,208;43;583;665;280;792;151;30;651;42;728;734;183;656,657;667;6;35;42;714,715,716;25;232,414;35;25,221;25;213,214;26;667;490;6;9,31,173;35;14,293;554,767;667;722;25;35;42;180;470;42;14,87;750;33;450;1;728;607;472;6,238;346;667;21,214,542,608;40;389;9,31;35;30;739;316;619;314;35,562;6,174,175,176;587;670;667;270,271;35;313;153;453,454;357;529;9,31;667;667;316;77,148;3;21,22;26;153;667;43,386,518;30;667;147;7;712;465;42,283;25;667;35,115;35,115;43;240;30;35;728;728;728;588;16,58,59,60;792;465;465;367;303;6,9,154,544;267;23;20,35;288;614;99,144;232,233;212;35;348;806;35;132,133,134;801;6;361;35;805;35;6;202,232,233,234;191;41;717,718;14;721;370;277;277;9,31;355;772;90;719;6;759;9,31;739;80;15,43,56;721;6,95;35,115;35;40;204;758;43;40,43,239;665;244;6,23;42;6,174,175,176;715;30;714,716;324;667;7,43,526;6;43;214,565,566;25,26;145;212;680;35,600;30,202;30,202;340;253,254;667;323;6,41;103,104;22,43;6,174,175,176;3;6,174,175,176;26;26;783;667;552;6,174,175,176,177,178;35;6;43,183;6,494;35;6,64,65;770;605;6;664;9,31;29,30;501;6;781;471;154;42;42;470;652;226;35,42;21,22;219;569;645;119;461;25;289,290;42;94;531;399;6;727;6;739;183;300,467;35;87,195;278,279;14;679;35;334,357;35;89;43;802;183;353;667;156;162;162;476;26;6,69,99,183,358;77,148;667;7;720;23,35;23,35;788;519;6,57;212;35;667;35;24;630;283;42;145,212;6,21,22;43;635;30,202;533;25;152;660;379;223;445;445;445;768;506;6;6,530;435;667;207,208;30;42;154,196,197;115;115;218;14,16;25,580;6,7,23,24;508;310;9,31;372;792;341;728;728;728;728;728;728;728;728;728;728;728;241;212;267;485;777;602;491,492;42;212;717,718;9,31;42;581;667;667;733;232,233;337;388;14,19,99,375;362;204;87,482,483;41,113;42,586,795,-797;392;529;145;14,593;667;9,31;35,154;23,35;405;6;667;6,8,48;35,115;35,115;14,16,20;227;816;283;817;318;403;760;9,31;40;710;539;256;475;736;615,616,617,618;7,100;35,212;287;6;6,7;43;6,82;205,206;6,49;43;6,21,66,67;9,31;703;667;721;312;445;26;9,31;667;22,63;694,695,696,697;667;9,31;776;667;6,174,175,176,177,178;567;9,31;99,239;428;6,23,415;268,723;658;25;25;637;399;385;774;749;720;212;534;25;25;470;220;357;541;736;6;77;6;809;667;465;42;192,647,648;42;109;137;488;25;89,119;798;250;6;49;667;343;274;25;25,43;6,42;154;630;9,31;399;35,115;87;35;711;369;212;77;266;514;748;6,49;10,22;31,136;42;357;56;581,720;195;32,542,624,625;262;328;77,148;35;201,202,203;35;576;80;667;71,72,73;568;736;357;166;6,23;42;10,14,32;25;445;297;23,35;441;89,542;667;728;714,715,716;714,715;212;9,31;30,38;22,43;153,154,155;339;740;35;263;728;728;728;728;728;728;728;728;728;728;728;728;728;728;728;728;638;120,143,192,193;25;6,21,49;469;252;737,738;789;25;388;212;200;35,49;403;6;7;667;89,655;787;121;19,85,386;735;143,225;35;14;480;384;667;402;315;667;42;288;35;9,31;728;782;-372;35;667;23;6;137;35,115;89,655;286;42;42;89,119;85;222;232,233,234;6;301;422;599;30,526,785,786;25;464;667;35;9,31;110,111;221,545;6,85;667;94;759;9,31;667;7,14;736;667;517;6;9,31;364;9,31;157;9,31;667;41;389;626;42;6;207,208;80;25;231;520;791;380,381,382,383;736;6;218,441;299;470;212;25;89,655;17;446;746;730;457;115;568;700;709;667;667;667;290;6,7;584;667;208;667;6,416;42;778;474;801;9,31;42;516;1;666;212;25;228;25;35,600;667;452;6;25;721;35;432;611;693;42;42;558;115;321;25;271,794;667,720;725;35;213,214;25;665;204;317;275;667;667;140;736;55;597;67,99,100;306;49;793;89,655;430;780;575;14;23,35;728;23,240;40;207,208;322;715;77,212;26;755;30,38;30,38;341;198;25;654;10,43;30;725;728;728;728;728;728;43;6;546;627;281;25;403;23,35;9,31;6;9,31;215;42;501;457;218;7,14;224;9,31;89;6,21;435;16;35;14,16,69;6;214,487;667;94;43;35;667;720;6;218;667;667;667;43,59,65;40;14;609;6,7;603;457;525;21,22;35;153;152;713;42;42;667;9,31;589;1;131;357;728;430,431;8,23;725;678;23,35;667;667;747;14,20,23;19;265;667;42;450;214;485;481;667;68;9,31;115,190;6,23,30,41,85,691;49;21,99,630;89;9,31;445;83;667;30,707,708;9,31;667;23;725;575;812;337,720;14;184;35;667;808;291;35,212;35,59;591;9,31;667;212,240;728;389;76;585;7;667;49;20;79,456;212;667;42;89;143;667;667;42;25;42;96;261;6;6,8,21;288;6,685;14;801;667;35,99;162;579;306;212;123,124,125,126,127,128,129;634;748;766;344;357;7,14,15;24,35,207;9,31;6,94,101;736;667;30,167;30,189;667;6,49;676,677;68;742;545;546;611;370;667;667;667;77;667;667;55;182;6;763;763;801;23,35;181;35,89;214;380,381;35,212;8,49;6;14,16,19,69,85,86,163;30,38;25;523;556;347;6;232,233,234,247,248,249;85;432;728;728;116;26;25,26;473;266;35;43;95;8,47,48;725;46;9,31;667;437;601;6,104,663;6,139;42;698,699;314;327;612;332;135;377;555;43,59;570;35;667;-372;667;667;14;493;577;32,119;6;22,63;12,13;667;6;9,31;667;417;667;8,9,10;9,31;35,212;35;14,49;667;43,104;667;389;303;76;168;35;35;14,16,19,86;42;45;182;434;229;230;510;115;182;6;6,23;14;612;720;9,31;323;389;145;306;81;6;27,30,122;9,31;9,31;194;445;357;42;715;35;667;395;667;214;701;725;721;152;42;154;162,628;801;374;803;19,563;9,31;9,31;6,104,117,144;546;255;715;7,14;14;99;35;6,174,175,176,177,178;43;667;724;667;6;316;391;686;606;667;667;14,373;667;6;667;378;185;721;721;801;218;496;55;35;667;667;667;763;667;9,31;357;35;35;731;115;35,36,37;30,38;30,38;470;629;721;380,381;85;380,381;30;6;667;645;365;319;121,214,486,487;146;105,106;6,85;23,25;481;667;461;99,107;6,550;21,22;412,413;667;330;191;9,31;35;43,104;402;470;598;667;389;667;16;49;242;20;35;743;636;521;736;10,31,497,692;43;89;9,31;7;23,35;6;667;6;42;746;35;6;667;43;640;542,571;42;667;316;24,35;6,7;6;288;49;188;661;148;667;674,675;294;115;468;14;9,31;464;721;309;6;478;470;720;451;257;495;440;217;6,90;114;721;30,38;336;11,35,633;667;49;231;667;42;6;70;470;667;667;85;7,14,16;232,233,234,235;344;667;39;402;212;232,233,234;311;667;85;667;801;99,239;6;35;23,43;43;35,55;462;25;56;9,31;736;9,31;35,41;118;218;762;9,31;35;632;3;216;224;121;7,43,375;42;9,31;67,99;43,101;457;94;6,174,175,176,177,178;667;42;667;667;3;481;264;752;35;462;30,38;771;744;9,31;30,199;9,31;30,38;9,31;667;784;665;97;305;9,31;665;19,813;76,77;42;97,98;6,25,66,78;9,31;30;484;6;736;401;6;745;404;23,25,112;667;6,650;14,56;79;630;340;145;667;7,43,59;386;14;667;436;25;667;43;646;6,174,175,176;6,95;667;16,49;35;6;720;6;470;295;488;179;94;350,351;789;641;667;642,643,644;6,63;430;145;145;372;731;512;667;320;22,63;33,34;425;667;41;26;43,338;9,31;298;34;131;35;470;6;25;9,31;667;354;43,49;6,99;729;101;704;9,31,183;682;408;28;6,394;380,381;568;9,31;409;214,564;94;7,16,19,443;667;667;158,159,160,161,162;667;667;543;801;667;214,487,499;35;6,702;6;10,31,497,692;30,38;557;276;6,99;6,7;25;612;667;6,9,31,174,175,176,177,178;553;322;438;667;667;667;61,62;221,545,572,573;30,38;30,38;30,38;402;402;479;134;720;30,38;6;408;667;6;801;303;43,44;801;42;238,363;331;316;337;818;9,31;668;667;6,10,444;6;462;667;303;14,49;667;672,673;6,174,175,176;30,38;35;9,31;7,14,19;6,19;458;2;14;40;9,31;9,31;357;9,31;7,14;389;82;23;89;667;6;667;55;418;504;690;721;667;701;701;701;115;779;9,31;43,59;326;288;9,14,31,41,409,684;667;10,31,32;667;8,27,50,51,52,53,54;667;801;507;9,31;6,79;667;470;667;55;667;515;337;667;683;6;448;667;667;108;631;667;667;424;406;726;452,542,582;667;607;470;145;6,66,67,174,175,176;667;653;329;116;49;35;35;30;721,736;399;30,38;6,550;14,21,22;528;667;667;667;9,31;667;41;667;142,143;7,100;35;35;7,14;6;80;274;22,63;14,49;35;117;42;10,43;470;470;720;667;667;9,31;667;639;14;667;307;6,99;6,59;667;532;35;359;662;6;6;667;303;407;9,31;9,31;667;55;701;8,10;71;604;7;6;46;6;8,10;667;337;25,35;667;274;667;721;667;704;667;667;9,31;801;9,31;165;322;720;9,31;732;783;667;801;801;15,16,400;89;535,536;35;667;485;182;667;6,7,18,19,20;623;25;6,174,175,176,177,178;667;407;6,7,35,84;419;447;9,31;21,22;402;269;94;153;30,38;667;214,542;801;55;462;-769,769;6,101;282;820;801;574;8,21,59,85,477;40;667;667;6;360;9,31;667;345;667;489;667;485;667;316;14;23,74,75;377,410;9,31;801;238;6,7;9,31;42;667;292;667;85;667;667;439;35;721;55,435;667;14,15,16;30,38;372;9,31;150;272;667;6,8,21;463;6,411;6;130;35,209,210,211;319;325;631;317;701;14;6,49;731;747;25;667;302;480;89;8,9,35,41;667;6;6;667;667;308;667;9,31;35;389;6,7,93;30,38;9,31;753;423;6,174,175,176;797;14;667;30,38;6,49;6,8,412;1,35;667;752;16,24;667;43,59;667;21,102;16;30,38;461;524;154;455;798;68;667;667;667;667;20;7,14,15;306;30,38;667;6,7;667;6;35;9,31;667;35;667;30,38;393;100;420,421;433;85;667;6;6;204;548;35,120;9,31;667;14;667;540;6,23,671;667;667;667;19;30,38;500;9,31;35;141;667;284;245;801;30,38;667;667;42;6;30,38;238;815;30,38;30,38;667;30,38;549,669;667;30,38;115,195;3;19;30,38;30,38;21,22;799;3;40;6,174,175,176,177,178,622;40,101;667;15,16,88;667;697,705,706;35;578;76;667;25;35,335;43;288;783;30,38;783;6,11;748;22,59,214;6;30,38;30,38;470;23,56;800;30,38;10,22;6,9;6;538;91;748;349;14,49;6;5;23,26,49,452,751;748";
        const arglistRefs = $scriptletArglistRefs$.split(';');
        for ( const i of todoIndices ) {
            for ( const ref of JSON.parse(`[${arglistRefs[i]}]`) ) {
                todo.add(ref);
            }
        }
    }
}

if ( $hasRegexes$ ) {
    const $scriptletFromRegexes$ = /* 0 */ [];
    const { hns } = entries[0];
    for ( let i = 0, n = $scriptletFromRegexes$.length; i < n; i += 3 ) {
        const needle = $scriptletFromRegexes$[i+0];
        let regex;
        for ( const hn of hns ) {
            if ( hn.includes(needle) === false ) { continue; }
            if ( regex === undefined ) {
                regex = new RegExp($scriptletFromRegexes$[i+1]);
            }
            if ( regex.test(hn) === false ) { continue; }
            for ( const ref of JSON.parse(`[${$scriptletFromRegexes$[i+2]}]`) ) {
                todo.add(ref);
            }
        }
    }
}

// Execute scriptlets
if ( todo.size && todo.has(0) === false ) {
    const $scriptletFunctions$ = /* 21 */
[preventAddEventListener,abortCurrentScript,abortOnPropertyRead,preventSetTimeout,setConstant,abortOnPropertyWrite,removeAttr,noEvalIf,preventSetInterval,trustedReplaceXhrResponse,jsonPrune,abortOnStackTrace,preventFetch,trustedSuppressNativeMethod,noWindowOpenIf,adjustSetInterval,trustedReplaceArgument,preventXhr,trustedSetConstant,adjustSetTimeout,trustedReplaceOutboundText];
    const $scriptletArgs$ = /* 689 */ ["scroll","$","modal_newsletter","/^(mouseout|mouseleave)$/","pum_popups","show-login-layer-article","document.oncontextmenu","disableSelection","document.ondragstart","reEnable","disable_copy","","keyCode","Promise","document.onmousedown","document.onselectstart","mb.advertisingShouldBeEnabled","false","ctrlKey","document.onkeydown","document.oncopy","disableEnterKey","keydown","oncontextmenu","contextmenu","onload","beforepaste","preventDefault","nocontext","jQuery","/copy|cut|paste|selectstart/","pop","/keydown|keyup/","console.clear","disabledEvent","onpaste","#tr_mesaj > td > .text-input.validate\\[required\\]","oncontextmenu|ondragstart|onselectstart","stopPrntScr","copy","/copy|keydown/","/^(?:copy|paste)$/","undefined","nocontextmenu","dragstart","document.onclick","mdp","onselectstart","/copy|contextmenu/","disableselect","trueFunc","/contextmenu|selectstart|copy|dragstart/","cpp_loc","disable_hot_keys","x5engine.utils.imCodeProtection","null","/contextmenu|select|copy/","oncontextmenu|ondragstart|onselectstart|onkeydown|oncopy|oncut","0x","matchMedia","shortcut","body","complete","_0x","document.addEventListener","alert","oncontextmenu|onDragStart|onSelectStart","oncontextmenu|onselectstart","/contextmenu|copy|selectstart/","document.onkeypress","debugger","onkeydown","oncontextmenu|onselectstart|onmousedown","oncontextmenu|onselectstart|style","#body_game","addEventListener","oncontextmenu|onselectstart|ondragstart","overlay","/,\"category_sensitive\"[^\\n]+?\"follow_button\":\\{\"__typename\":\"CometFeedStoryFollowButtonStrategy\"[^\\n]+\"cursor\":\"[^\"]+\"\\}/g","}","/api/graphql","require.0.3.0.__bbox.define.[].2.is_linkshim_supported require.0.3.0.__bbox.define.[].2.click_ids","noopFunc","killCopy","oncontextmenu|ondragstart|onselectstart|onkeydown","document","/^(?:contextmenu|copy|keydown)$/","oncontextmenu|onselectstart|onselect|oncopy","Drupal","killcopy","/contextmenu|keydown|keyup|copy/","eval","Source","pagelink","runPageBugger","document.body.oncontextmenu","securityTool.disableRightClick","securityTool.disableF12","securityTool.disableCtrlP","securityTool.disableCtrlS","securityTool.disablePrintScreen","securityTool.disablePrintThisPage","securityTool.disableElementForPrintThisPage","getSelection","quoty-public","html","console.dir","navigator.userAgent","devtoolIsOpening","#VdoPlayerDiv","devtoolsDetector","a#download_link","stay","Drupal.CTools.Modal.show","/(^(?!.*(injectedScript|makeProxy).*))/","/keydown|mousedown/","disable_keystrokes","/contextmenu|keydown/","Object.prototype.preroll","[]","check","openOverlaySignup","concertAds","AudiosL10n","/contextmenu|copy/","debug","AdBlocker","devtool","navigator","devtools","setInterval","stateObject","setTimeout","RegExp","mousedown","dispatch","popupScreen","flashvars.autoplay","mouseout","openLayer","blockFuckingEverything","build.js","elements",".entry-content","wccp_pro","clear_body_at_all_for_extentions","mensagem","[oncontextmenu=\"return false;\"]","/contextmenu|keyup|keydown/","mouseleave","preventDeleteDialog","phimv","devtoolsOpen","String.fromCharCode","Object.prototype._detectLoop","forbiddenList","_detectLoop","detect","DD","disabledKeys","/adsbygoogle|ad-manager/","/devtool|console\\.clear/","123","Object.prototype.disableMenu","Function.prototype.constructor","\"debugger\"","abort","Object.prototype.browserDetectorService","{}","Object.prototype.browserDetectorService.isBrowserChrome","afterKeydown","void","devtoolsDetector.launch","oncontextmenu|ondragstart","/select|copy|contextmenu/","document.body.onselectstart","googlesyndication","DevToolsOpen","ABB_config","hmwp_is_devtool","jh_disabled_options_data","/cut|copy|paste|contextmenu/","oncontextmenu|ondragstart|onselectstart|onload|onblur","login_completed","true","disableclick","/mainseto.js:286:1","ays_tooltip","console.log","console.table","123===i","/^(contextmenu|copy)$/","clickIE4","oncopy|oncut","disableRightClick","layerid","1","html[onselectstart]","/contextmenu|copy|cut|key/","[arguments];","key","/copy|selectstart/","return","/preventDefault|pointerType/",".all-lyrics","[native code]","#__next","j.value--","1000","0.001","img[no-copy=\"true\"]",".viewer-container",".trackContainer",".fancybox-container","blockEvent","String.prototype.includes","0","condition","preview-cms","/^(?:pointerdown|mousedown)$/",".js-pachete-online-internet2","event.dispatch","uxGuid","killads","www3.doubleclick.net","PASSER_videoPAS_apres","ads_enabled","adsbygoogle","load","adblock","pro-modal","doubleclick","length:10",".getState();","4500","holidAds","detectAdBlock","String.prototype.endsWith","/edit","Storage.prototype.setItem","json:\"DWEB\"","DWEB_PIN_IMAGE_CLICK_COUNT","json:\"\"","unauthDownloadCount","blur","ThriveGlobal","blazemedia_adBlock","addLink","_sp_","100","document.getElementById","advert-tester","nebula.session.flags.adblock","_adBlockCheck","webkitRequestFileSystem","abde","ads","2000","/^(?:contextmenu|copy|selectstart)$/","/^(?:contextmenu|copy)$/","/^(?:contextmenu|keydown)$/","onbeforeunload","valid_user","Drupal.behaviors.detectAdblockers","scan","500","oncopy","AdBlock","#sign-up-popup","adBlockDetected","ADBdetected","onload_popup","8000","_sp_._networkListenerData","ad-blocker",".ab_detected","adMessage","tweaker","$adframe","BIA.ADBLOCKER","Adblocker","10000","()","samDetected","4000","ABDSettings","adBlockFunction","block","hidekeep","checkAds","google_jobrunner","#advert-tracker","3000","isAdblockDisabled","clickIE","checkPrivacyWall","loadOutbrain","intsFequencyCap","w3ad","restriction","adsAreShown","1500","bioEp.showPopup","Date.prototype.toUTCString","abd","innerHTML","intializemarquee","oSpPOptions","detector_active","aoezone_adchecker","oncontextmenu|ondragstart|onkeydown|onmousedown|onselectstart","message","preventSelection","fuckAdBlock","pageService.initDownloadProtection","a1lck","adsBlocked","/^(?:keyup|keydown)$/","detectPrivateMode","addLinkToCopy","_sharedData.is_whitelisted_crawl_bot","showOverlay","NoAd","loginModal","700","document.documentElement.oncopy","oncontextmenu|onkeydown|onmousedown","confirm","ads_not_blocked","disable_in_input","can_i_run_ads","__cmpGdprAppliesGlobally","stopSelect","warning","ytInitialPlayerResponse.auxiliaryUi.messageRenderers.upsellDialogRenderer","auxiliaryUi.messageRenderers.upsellDialogRenderer","visibilitychange","/bgmobile|\\{\\w\\.\\w+\\(\\)\\}|\\.getVisibilityState\\(\\)/","document.visibilityState","json:\"visible\"","hideBannerBlockedMessage","__ext_loaded","slideout","faq/whitelist","_sp_.mms.startMsg","blurred","height","document.getElementsByTagName","RL.licenseman.init","abStyle","modal","offsetHeight","ga_ExitPopup3339","t.preventDefault","ai_adb","none","replaceCopiedText","oncontextmenu|onselectstart|ondragstart|oncopy|oncut|onpaste|onbeforecopy","ABD","ondragstart","better_ads_adblock","onselectstart|ondragstart","console.debug","which","window.addEventListener","/^(contextmenu|copy|dragstart|selectstart)$/","alerte_declanchee","initimg","oncontextmenu|onCopy","adBlock","oncontextmenu|onmousedown|onselectstart","appendMessage","document.body.setAttribute","5000","vSiteRefresher","{e(n,t,r)}","30000","popup","banner","/contextmenu|selectstart|copy/","oncontextmenu|ondragstart|onselectstart|onkeydown|onmousedown","oncontextmenu|onkeydown","adtoniq","ondragstart|onselectstart","/contextmenu|copy|keydown/","/^(contextmenu|keydown)$/","a","adblocker","exit_popup","adsEnabled","locdau","show","ondrop|ondragstart","onselectstart|ondragstart|oncontextmenu","div.story_text","document.body.oncopy","test.remove","noscroll","onmousemove|ondragstart|onselectstart|oncontextmenu","/contextmenu|selectstart/","ai_check","bait","onselectstart|ondragstart|onmousedown|onkeydown|oncontextmenu","window.SteadyWidgetSettings.adblockActive","adblockerdetected","juicyads","gdpr_popin_path","showEmailNewsletterModal","generatePopup","dragstart|keydown/","/contextmenu|keydown|dragstart/","oncontextmenu|onselectstart|ondragstart|onclick","btoa","f12lock","checkFeed","visibility","style","div#novelBoby","HTMLIFrameElement","FuckAdBlock","samOverlay","adStillHere","tjQuery","oncontextmenu|onMouseDown|style","/^(?:contextmenu|copy|keydown|mousedown)$/","document.onkeyup","commonUtil.openToast","adb","NS_TVER_EQ.checkEndEQ","nd_shtml","canRunAds","Adblock","isNaN","mps._queue.abdetect","contribute","devtoolschange","ondragstart|oncontextmenu","clickNS","newsletterPopup","onContextMenu","premium","onkeydown|oncontextmenu","oncontextmenu|oncopy","abp","/contextmenu|cut|copy|paste/","blocked","blocker","SignUPPopup_load","oncontextmenu|onselectstart|onselect|ondragstart|ondrag","removeChild","_0xfff1","event","stopPropagation","/contextmenu|mousedown/",".modal","soclInit","Zord.analytics.registerBeforeLeaveEvent","myModal","an_message",".height","admrlWpJsonP","oncopy|oncontextmenu|onselectstart|onselect|ondragstart|ondrag|onbeforeprint|onafterprint","disable_ext_code","adsbygoogle.length","pipaId","append_link","/^(?:contextmenu|dragstart|selectstart)$/","ai_front","ansFrontendGlobals.settings.signupWallType","journeyCompilerGateway","pgblck","/dragstart|keyup|keydown/","/keyup|keydown/","wpcc","oncopy|oncontextmenu","oncontextmenu|ondragstart|oncopy|oncut",".select-none","carbonLoaded","/contextmenu|cut|copy|keydown/","initAdBlockerPanel","String.prototype.charCodeAt","ai_","forceRefresh","head","/copy|dragstart/","/getScript|error:/","error","AdB","oncontextmenu|ondragstart|onselectstart|onselect|oncopy|onbeforecopy|onkeydown|onunload","selectionchange","quill.emitter","oncontextmenu|onDragStart|onselectstart","/contextmenu|selectstart|select|copy|dragstart/","adLazy","_0x1a4c","jQuery!==\"undefined\"","clearInterval(loginReady)","document.body.onmouseup","addCopyright","selectstart","&adslot","copy_div_id","oncontextmenu|onkeydown|onselectstart","LBF.define","oncopy|oncontextmenu|oncut|onpaste","input","oncontextmenu|oncopy|onselectstart","onbeforecopy|oncontextmenu|oncopy|ondragstart|onmouseup|onselect|onselectstart","oncontextmenu|ondragstart|onkeydown|onmousedown|onselectstart|style","SD_BLOCKTHROUGH","body[style=\"user-select: none;\"]","cookie","b2a","ab","oncopy|oncut|onselectstart|style|unselectable","document.body.oncut","/copy|cut|selectstart/","oncontextmenu|onselectstart|oncut|oncopy","oncontextmenu|ondragstart|onselect","encodeURIComponent","inlineScript","donation-modal","isMoz","Delay","/contextmenu|dragstart|keydown/","event.dispatch.apply","document.querySelector","gif","DOMContentLoaded","rprw","\"input\"","contentprotector","update_visit_count","replace","test","onscroll","5500","login","showAdblockerModal","dfgh-adsbygoogle","oncontextmenu|ondragstart|ondrop|onselectstart","[oncontextmenu]","jsData.hasVideoMeteringUnlogEnabled","lepopup_abd_enabled","広告","document.referer","Object.prototype.bgOverlay","Object.prototype.fixedContentPos","oncontextmenu|ondragstart|onkeydown|onmousedown|onselectstart|onselect|oncopy|onbeforecopy|onmouseup","onContextmenu|onMouseDown|onSelectStart","kan_vars.adblock","attachToDom","ad-fallback","document.createElement","createAdblockFallbackSubscribeToProtopageAdDiv","gnt_mol_oy","adsok","length","nouplaod","img[oncontextmenu=\"return false;\"]","Object","/(?=^(?!.*(jquery|inlineScript)))/","ab_tests","scribd_ad","admiral","/contextmenu|copy|drag|dragstart/","userAgent","analytics","googlebot","document.querySelectorAll","/contextmenu|keydown|keypress|copy/","sneakerGoogleTag","/_0x|devtools/","checkAdblockBait","onclick","[onclick=\"myFunction()\"]","wccp_pro_iscontenteditable","return\"undefined\"","ready","3","Time_Start","i--","0.02","/hotjar|googletagmanager/","Clipboard","ad","whetherdo","devtoolsDetector.addListener","Premium","SteadyWidgetSettings.adblockActive","||null","DisDevTool","/googlesyndication|googletag/","googletag","count","initials.layout.layoutPromoProps.promoMessagesWrapperProps.shouldDisplayAdblockMessage","mtGlobal.disabledAds","/DevTools|_0x/","throwFunc","ANN.ads.adblocked","cloudflareinsights.com","pleaseSupportUs","nn_mpu1","maxUnauthenicatedArticleViews","googletag.cmd","rocket-DOMContentLoaded","bind(document)","innerHeight","/^(contextmenu|mousedown|keydown)$/","placeAdsHandler","ramp.addUnits","pqdxwidthqt","document.fullscreenElement","browser-plugin","nitroAds.loaded","checkDevTools","topMessage","forbidDebug","2","RegExp.prototype.toString",".join(\"\")","DisableDevtool","/isEnable|isOpen/","nitroAds","getComputedStyle","viewClickAttributeId","ad-wrap","__NEXT_DATA__.props.pageProps.adPlacements","/contextmenu|selectstart|dragstart/","loadexternal","/,\"expanded_url\":\"([^\"]+)\",\"url\":\"[^\"]+\"/g",",\"expanded_url\":\"$1\",\"url\":\"$1\"","/graphql","/,\"expanded_url\":\"([^\"]+)\",\"indices\":([^\"]+)\"url\":\"[^\"]+\"/g",",\"expanded_url\":\"$1\",\"indices\":$2\"url\":\"$1\"","/tweet-result","style.display","clipboardData","console","/Timeout\":\\d+/","Timeout\":0","/api/v","linkPrefixMessage","adb-enabled","Array.prototype.includes","visitor-gate",".LoginSection","document.getSelection","detect_modal","disableCTRL","counter",".html","RegExp.prototype.test","\"contact@foxteller.com\"","onselectstart|oncopy","json:\"freeVideoFriendly\"","freeVideoFriendlySlug","(!0)","HTMLImageElement.prototype.onerror","player.pause","/stackDepth:(9|10).+https:[./0-9a-z]+\\/video\\.[0-9a-f]+\\.js:1\\d{2}:1.+\\.emit/","/[0-9a-f]{40}\\.js:1\\d{2}([\\S\\s]+\\.emit.+core\\.){3}/","PieScriptConfig","method:HEAD","location.href","function(t)","ad_blocker_detector_modal","clientHeight","String.prototype.trim","iframe","nonframe","Object.prototype.dbskrat","show_modal","href","[href*=\"ad.adverticum.net\"]","showFbPopup","FbExit","navigator.registerProtocolHandler","mailto","e","data.page_content.slot_widgets","ad-block","typeof loadElement","json:\"header\"","/^[A-Za-z]{12}$/","/^data:text\\/javascript/","ad_allowed","e=>e-1",".abort();"];
    const $scriptletArglists$ = /* 822 */ ";0,0;1,1,2;0,3;2,4;3,5;1,6;2,7;1,8;1,7,9;2,10;0,11,12;3,1;1,1,13;2,6;2,14;2,15;4,16,17;0,11,18;2,19;2,20;5,21;5,8;1,19;0,22;6,23;1,1,24;2,25;0,26;7,10;0,24,27;2,28;1,29,22;0,30;3,31;0,24;0,32,12;1,33;0,22,34;6,35,36;6,37;5,38;0,39;5,6;0,40;0,41,42;1,43;0,44;2,43;1,15;4,6,11;4,15,11;4,19,11;4,14,11;4,45,11;0,11,46;6,47;0,48;5,14;5,15;4,49,50;0,51;2,52;2,21;1,29,23;0,11,42;5,53;5,10;1,14;2,8;4,54,55;0,56;6,57;0,11,58;1,59;2,60;6,23,61,62;8,63;1,64,15;1,20;2,65;6,66;6,67,61;0,68;1,29,39;1,29,24;2,69;8,70;2,45;6,23,61;6,71;6,72,61;6,73,74;1,75,18;6,76;1,7;1,29,77;9,78,79,80;10,81;5,7;5,28;1,49,9;1,8,6;4,28,82;4,7,82;5,83;6,84;1,29,85;0,86;1,6,15;6,87;1,29,88;1,9,89;0,90;1,91,24;4,33,42;0,39,92;0,39,93;1,94;1,69;4,19,50;0,39,27;1,95;4,96,82;4,97,82;4,98,82;4,99,82;4,100,82;4,101,82;4,102,82;11,103,104;1,64,24;6,23,105;4,106,82;4,107,11;4,108,82;1,21;1,33,24;6,23,109;4,110,42;6,23,111,112;11,113,114;0,115;4,6,50;5,116;0,117;4,118,119;1,60;1,120,70;2,121;3,122;1,123;3,70;0,124;4,33,82;8,125;7,126;1,29,127;1,23;1,128,129;1,130,131;1,132,70;2,110;1,29,12;1,133,70;0,134,135;3,136;6,47,61;4,137,11;0,117,27;0,138,139;0,11,140;11,91,141;0,134,11,142,143;1,9;1,29,144;1,145;4,28,42;4,53,42;5,146;6,23,147;0,148;0,149;5,19;0,24,63;11,64,150;11,107,151;4,152,17;7,65;7,153;4,154,42;8,33;4,15,50;4,69,50;4,155,119;3,156;8,157;4,158,50;1,133,24;0,22,159;12,160;8,161;0,22,162;4,163,17;13,164,165,166;4,167,168;4,169,50;8,127;3,127;0,170;0,22,171;0,39,171;4,172,82;4,14,55;4,6,55;6,173,11,62;0,174;2,175;12,176;8,177;5,178;4,14,82;1,29,179;4,180,55;0,181;0,134,42,142,61;6,182;4,183,184;1,14,185;11,1,186;1,75,187;6,47,11,112;4,33,50;4,188,50;4,189,50;0,22,190;2,23;0,191;2,103;5,192;4,110,168;6,193;1,133,194;14,195,196;6,47,197;0,198,11,142,85;0,22,199;0,22,200;0,201,202;0,24,203;0,44,11,142,204;0,24,205,142,206;15,207,208,209;0,24,11,142,210;0,24,27,142,211;4,14,50;0,134,11,142,212;0,134,11,142,213;0,11,214;16,215,216,11,217,218;0,219,11,142,220;0,24,221;2,222;4,223,184;12,224;4,225,216;4,226,184;3,227;3,126;0,228,229;3,230;12,231;17,176,232;3,176;3,233,234;3,235;4,236,82;16,237,216,11,217,238;16,239,216,240,217,241;16,239,216,242,217,243;0,244;3,245;2,246;5,247;5,248;3,120,249;1,250,251;4,252,42;2,247;4,253,184;4,254,82;2,255;3,256,257;0,258;0,259,27;0,260;2,261;4,262,184;4,263,82;3,264,265;6,266;1,29,267;1,29,268;5,269;4,270,82;3,271,272;2,273;1,250,274;1,250,275;5,276;1,29,277;5,278;4,229,17;4,279,17;3,280,281;1,29,42;3,282,257;4,283,184;3,282,284;1,29,256;2,285;4,286,50;1,250,287;5,288;4,289,50;5,285;4,290,184;3,291,265;3,282,292;1,64,65;4,293,184;3,282,208;5,294;4,295,82;5,296;2,297;3,298;1,250,42;1,29,299;4,300,184;3,282,301;3,302;2,303;4,304,17;3,305;5,306;2,307;4,308,184;4,309,184;6,310;1,311,294;1,312;2,313;4,314,82;0,138,31;5,20;2,315;3,316;0,317;4,318,82;4,254,42;4,227,55;1,1,244;5,319;4,320,184;3,321;3,322,272;3,323,265;3,282,324;2,325;6,326;2,327;4,328,184;0,22,329;1,1,228;0,22,27;2,330;2,331;5,332;3,333;4,334,42;10,335;0,336,337;18,338,339;4,340,184;3,341;2,49;3,342;3,343;2,344;4,345,17;8,346;1,347,55;2,348;5,9;0,39,103;2,349;3,350;1,91,304;3,351;2,352;0,11,353;1,29,354;3,229;1,250,355;0,39,356;6,357;5,358;1,1,42;5,359;4,360,216;6,361;1,64;1,6,200;4,362,50;1,75,363;1,364,18;0,365;3,61;2,366;5,367;6,368;4,369,17;6,370;3,55;2,358;0,11,256;3,371;2,372;3,282,373;2,269;3,374;3,375,376;3,377;1,250,378;0,379;6,380;6,381;2,382;6,383;0,384;17,176;0,385;4,6,42;1,29,53;0,24,386;3,387;3,388,281;4,389,184;2,390;3,391;6,392;1,25;6,393,394,62;2,395;3,396;6,173;1,1,351;3,397,292;3,227,373;6,398,61;0,399;3,290;1,29,400;1,250,229;1,25,24;3,401;1,1,39;6,402,61;4,360,55;4,403,17;1,250,404;1,1,405;5,406;1,1,407;5,408;7,23;0,409;0,410;6,411;1,1,412;6,67;0,11,63;4,413,17;3,414,208;8,415,208;6,416,417,112;4,15,55;2,418;0,11,382;5,419;4,269,17;3,420;3,421;2,422;6,423;0,424;2,53;4,425,55;4,8,55;4,426,55;3,427;4,428,50;2,429;2,430;1,1,431;1,91,432;4,433,55;1,64,434;0,435;6,436;2,437;3,351,249;1,132,438;6,439,61;4,313,50;3,269;3,440;6,441,61;6,442;4,443,17;0,444;3,445,208;3,446;5,49;3,447,373;4,19,82;6,448,61;8,449;6,37,61;2,450;1,451,452;4,103,42;0,453;3,454,208;1,455;3,456,292;3,457,292;1,64,27;3,458,265;5,25;1,1,459;4,19,55;2,460;3,63;4,6,82;0,138;6,461,61;8,350;1,10;1,53;5,462;1,75,463;3,464,216;1,1,267;2,465;1,1,369;0,466;5,467;4,468,42;5,469;3,470;5,69;0,259;0,471;0,472,473;4,25,55;6,474,61;5,460;6,475,476,112;2,477;0,478;4,8,82;4,15,82;2,479;1,480,481;1,29,27;3,482;3,256;3,483;0,484;1,1,485;1,75,22;0,486;0,11,487;6,488;0,489,490;6,491;0,492;0,228,493;2,494;0,39,495;8,496;5,395;4,497,55;2,498;0,499;3,500;2,501;6,502,61;2,503;6,504,505;6,506;6,507;6,508,61;4,20,55;4,509,184;8,351;6,416,510,112;1,250,511;8,227;3,481;2,512;4,513,17;4,430,184;6,514,61,112;4,515,55;4,395,55;0,516;5,120;6,517;6,518;11,519,520;3,521;1,250,522;4,69,55;6,502;3,523;1,23,22;0,524,525;1,6,43;1,15,49;1,526,229;17,527;0,528,529;1,1,530;1,29,452;0,11,200;2,531;1,532;1,91,533;1,1,534;3,535,536;3,537,373;1,538;1,38;8,539;4,8,50;6,540,541,62;4,542,42;4,543,11;3,544;3,108,249;1,188,545;11,480,481;1,64,71;4,546,82;4,547,82;3,443;6,548;6,549;2,550;4,289,82;4,38,82;6,37,61,62;1,551,552;11,553,554;3,555;3,556;1,28;3,557,292;4,7,42;11,250,558;6,23,559,112;11,6;11,560,561;1,562;0,149,563;11,553,564;0,565;1,29,566;12,567;1,133,568;1,569,229;0,570;1,64,39;2,571;3,129;8,572;1,573;6,574,575;1,64,22;2,576;0,453,577;0,528,578;4,395,55,579;4,175,55,579;4,95,55,579;4,580,216;15,581,11,582;17,583;15,584,208,209;1,576;3,585;12,256;4,6,55,579;0,528,228;0,22,12;4,154,82;3,586;2,587;4,6,184;3,588;4,589,17;3,590;11,33;4,591,42;12,592;14;0,24,42;2,593;1,553,564;1,347,564;4,564,82;0,24,205;19,594;4,20,82;0,138,511;4,595,17;4,596,184;8,597;4,33,598;4,599,17;12,600;3,601;3,602,373;4,603,55;0,528,256;8,256;2,604;0,605,606;0,138,607;0,608,27;4,609,82;8,110;4,610,82;7,70;4,611,17;4,612,184;0,486,613;4,614,184;2,615;3,227,257;4,616,82;4,617,82;4,229,618;1,619,620;4,621,82;11,13,622;2,623;8,624;19,625;17,256;0,228,626;4,627,42;0,628;15,629,208;2,419;9,630,631,632;9,633,634,635;0,39,11,142,206;0,528,636;0,39,637;1,133,638;9,639,640,641;0,336,135;0,39,642;3,643;16,644,216,42,217,645;3,646;11,647,520;3,648;1,19,649;4,327,82;15,650,208,209;0,489,651;13,652,653,166;6,506,61,62;6,654,61,62;0,24,577;16,239,216,655,217,656;15;3,657,272;1,6,27;4,658,42;11,659,660;11,659,661;2,662;12,227;12,663;1,65,664;0,134,665;3,666;3,667;20,668,669,670;4,671,184;4,672,82;6,416,61,112;6,673,674;1,553,132;0,149,675;3,676,292;16,677,216,82,217,678;8,679,208;10,680;3,681;3,682;16,250,216,683,217,684;1,64,27,685;4,686,184;19,687;3,688,208";
    const arglists = $scriptletArglists$.split(';');
    const args = $scriptletArgs$;
    for ( const ref of todo ) {
        if ( ref < 0 ) { continue; }
        if ( todo.has(~ref) ) { continue; }
        const arglist = JSON.parse(`[${arglists[ref]}]`);
        const fn = $scriptletFunctions$[arglist[0]];
        try { fn(...arglist.slice(1).map(a => args[a])); }
        catch { }
    }
}

/******************************************************************************/

// End of local scope
})();

void 0;
