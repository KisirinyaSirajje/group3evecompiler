// EveCompiler IDE Frontend JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const sourceCodeEl = document.getElementById('sourceCode');
    const lineNumbersEl = document.getElementById('lineNumbers');
    const compileBtn = document.getElementById('compileBtn');
    const clearBtn = document.getElementById('clearBtn');
    const sampleBtn = document.getElementById('sampleBtn');
    const sampleModal = document.getElementById('sampleModal');
    const closeBtn = document.querySelector('.close-btn');
    const statusContainer = document.getElementById('statusContainer');

    // Line numbers
    function updateLineNumbers() {
        const count = sourceCodeEl.value.split('\n').length;
        let nums = '';
        for (let i = 1; i <= count; i++) nums += i + '\n';
        lineNumbersEl.textContent = nums;
        lineNumbersEl.scrollTop = sourceCodeEl.scrollTop;
    }
    sourceCodeEl.addEventListener('input', updateLineNumbers);
    sourceCodeEl.addEventListener('scroll', () => {
        lineNumbersEl.scrollTop = sourceCodeEl.scrollTop;
        // Update highlight position when scrolling
        const highlight = document.getElementById('errorHighlight');
        if (highlight) {
            const textareaStyle = window.getComputedStyle(sourceCodeEl);
            const lineHeight = parseFloat(textareaStyle.lineHeight);
            const paddingTop = parseFloat(textareaStyle.paddingTop);
            const lineMatch = highlight.dataset.lineNum;
            if (lineMatch) {
                const topPosition = (parseInt(lineMatch) - 1) * lineHeight + paddingTop;
                highlight.style.top = topPosition + 'px';
            }
        }
    });
    updateLineNumbers();

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            switchTab(tabName);
        });
    });

    function switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected tab
        document.getElementById(tabName).classList.add('active');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    }

    // Compile button
    compileBtn.addEventListener('click', () => {
        const code = sourceCodeEl.value;
        if (!code.trim()) {
            showStatus('Please enter some code to compile', 'error');
            return;
        }

        compileBtn.disabled = true;
        compileBtn.textContent = '⏳ Compiling...';

        fetch('/api/compile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: code })
        })
        .then(response => response.json())
        .then(data => {
            compileBtn.disabled = false;
            compileBtn.textContent = '🚀 Compile';

            if (data.success) {
                showStatus('✅ Compilation successful!', 'success');
                document.getElementById('errorBadge').classList.add('hidden');
                // Remove any error highlight
                const existingHighlight = document.getElementById('errorHighlight');
                if (existingHighlight) existingHighlight.remove();
                displayOutput(data);
            } else {
                showStatus(`❌ ${data.error}`, 'error');
                const errCount = data.error.split('\n').filter(l => l.trim()).length;
                const badge = document.getElementById('errorBadge');
                badge.textContent = errCount + (errCount === 1 ? ' error' : ' errors');
                badge.classList.remove('hidden');
                document.getElementById('outputContent').innerHTML =
                    `<div class="error-message"><strong>Compilation Error:</strong><br>${escapeHtml(data.error).replace(/\n/g, '<br>')}</div>`;
                
                // Extract and highlight error line
                highlightErrorLine(data.error);
            }
        })
        .catch(error => {
            compileBtn.disabled = false;
            compileBtn.textContent = '🚀 Compile';
            showStatus(`Error: ${error.message}`, 'error');
        });
    });

    // Clear button
    clearBtn.addEventListener('click', () => {
        sourceCodeEl.value = '';
        sourceCodeEl.focus();
        statusContainer.classList.add('hidden');
        // Remove error highlight
        const existingHighlight = document.getElementById('errorHighlight');
        if (existingHighlight) existingHighlight.remove();
    });

    // Sample programs button
    sampleBtn.addEventListener('click', () => {
        loadSamples();
        sampleModal.classList.remove('hidden');
    });

    // Close modal
    closeBtn.addEventListener('click', () => {
        sampleModal.classList.add('hidden');
    });

    // Close modal on outside click
    sampleModal.addEventListener('click', (e) => {
        if (e.target === sampleModal) {
            sampleModal.classList.add('hidden');
        }
    });

    function showStatus(message, type) {
        const statusMsg = document.getElementById('statusMessage');
        statusMsg.textContent = message;
        statusMsg.className = `status-message ${type}`;
        statusContainer.classList.remove('hidden');
    }

    function displayOutput(data) {
        // Output tab
        let outputHTML = '<div class="success-message">✅ Compilation successful!</div>';
        outputHTML += '<h3>📈 Compilation Statistics</h3>';
        outputHTML += `
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Tokens</td>
                    <td>${data.statistics.tokens}</td>
                </tr>
                <tr>
                    <td>IR Instructions</td>
                    <td>${data.statistics.ir_lines}</td>
                </tr>
                <tr>
                    <td>Assembly Lines</td>
                    <td>${data.statistics.assembly_lines}</td>
                </tr>
            </table>
        `;
        document.getElementById('outputContent').innerHTML = outputHTML;

        // Tokens tab
        if (data.tokens && data.tokens.length > 0) {
            let tokensHTML = '<table><tr><th>Type</th><th>Value</th></tr>';
            data.tokens.forEach(token => {
                tokensHTML += `<tr><td>${escapeHtml(token.type)}</td><td><code>${escapeHtml(token.value)}</code></td></tr>`;
            });
            tokensHTML += '</table>';
            document.getElementById('tokensContent').innerHTML = tokensHTML;
        }

        // Symbol table tab
        if (data.symbol_table && Object.keys(data.symbol_table).length > 0) {
            let symbolsHTML = '<table><tr><th>Variable</th><th>Type</th></tr>';
            Object.entries(data.symbol_table).forEach(([name, type]) => {
                symbolsHTML += `<tr><td>${escapeHtml(name)}</td><td>${escapeHtml(type)}</td></tr>`;
            });
            symbolsHTML += '</table>';
            document.getElementById('symbolsContent').innerHTML = symbolsHTML;
        } else {
            document.getElementById('symbolsContent').innerHTML = '<p class="placeholder">No variables declared</p>';
        }

        // IR Code tab
        if (data.optimized_ir && data.optimized_ir.length > 0) {
            let irHTML = '';
            data.optimized_ir.forEach((line, idx) => {
                const isComment = line.includes(';');
                const commentClass = isComment ? 'code-comment' : '';
                irHTML += `<div class="code-line"><span class="${commentClass}">${escapeHtml(line)}</span></div>`;
            });
            document.getElementById('irContent').innerHTML = irHTML;
        }

        // Assembly tab
        if (data.assembly && data.assembly.length > 0) {
            let asmHTML = '';
            data.assembly.forEach(line => {
                asmHTML += `<div class="code-line">${escapeHtml(line)}</div>`;
            });
            document.getElementById('assemblyContent').innerHTML = asmHTML;
        }

        // AST tab
        if (data.ast_tree) {
            const astContainer = document.getElementById('astContent');
            astContainer.innerHTML = '';
            const svg = renderAstTree(data.ast_tree);
            astContainer.appendChild(svg);
        }

        // Switch to output tab
        switchTab('output');
    }

    function loadSamples() {
        fetch('/api/samples')
        .then(response => response.json())
        .then(samples => {
            const sampleList = document.getElementById('sampleList');
            sampleList.innerHTML = '';

            if (Object.keys(samples).length === 0) {
                sampleList.innerHTML = '<p>No sample programs available</p>';
                return;
            }

            Object.entries(samples).forEach(([name, code]) => {
                const item = document.createElement('div');
                item.className = 'sample-item';
                item.innerHTML = `
                    <h4>${escapeHtml(name)}</h4>
                    <p>${escapeHtml(code.substring(0, 50))}...</p>
                `;
                item.addEventListener('click', () => {
                    sourceCodeEl.value = code;
                    sampleModal.classList.add('hidden');
                });
                sampleList.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error loading samples:', error);
            document.getElementById('sampleList').innerHTML = '<p>Error loading samples</p>';
        });
    }

    function highlightErrorLine(errorMessage) {
        // Extract line number from error message (e.g., "Line 3:")
        const lineMatch = errorMessage.match(/Line (\d+)/);
        if (!lineMatch) return;

        const errorLineNum = parseInt(lineMatch[1], 10);
        const lines = sourceCodeEl.value.split('\n');
        if (errorLineNum < 1 || errorLineNum > lines.length) return;

        // Remove any existing highlights
        const existingHighlight = document.getElementById('errorHighlight');
        if (existingHighlight) existingHighlight.remove();

        // Get textarea properties
        const editorWrapper = document.querySelector('.editor-wrapper');
        const textareaStyle = window.getComputedStyle(sourceCodeEl);
        const lineHeight = parseFloat(textareaStyle.lineHeight);
        const paddingTop = parseFloat(textareaStyle.paddingTop);
        const paddingLeft = parseFloat(textareaStyle.paddingLeft);

        // Calculate position from the top of textarea content
        const topPosition = (errorLineNum - 1) * lineHeight + paddingTop;

        // Create highlight overlay
        const highlight = document.createElement('div');
        highlight.id = 'errorHighlight';
        highlight.dataset.lineNum = errorLineNum; // Store line number for scroll sync
        highlight.style.cssText = `
            position: absolute;
            left: 0;
            top: ${topPosition}px;
            width: 100%;
            height: ${lineHeight}px;
            background-color: rgba(255, 0, 0, 0.1);
            border-bottom: 3px solid #ff4444;
            pointer-events: none;
            z-index: 10;
            overflow: hidden;
        `;
        
        editorWrapper.style.position = 'relative';
        editorWrapper.style.overflow = 'hidden';
        editorWrapper.appendChild(highlight);

        // Scroll textarea to show error line
        const lineStart = lines.slice(0, errorLineNum - 1).join('\n').length + (errorLineNum > 1 ? 1 : 0);
        sourceCodeEl.focus();
        sourceCodeEl.setSelectionRange(lineStart, lineStart);
        
        // Scroll with some padding
        const targetScroll = Math.max(0, topPosition - lineHeight * 3);
        sourceCodeEl.scrollTop = targetScroll;
        lineNumbersEl.scrollTop = targetScroll;
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // ── AST Tree Renderer ────────────────────────────────────────

    function renderAstTree(root) {
        const NODE_W    = 160;
        const NODE_H    = 36;
        const H_GAP     = 18;
        const V_GAP     = 60;
        const FONT_SIZE = 12;

        // 1. Compute subtree widths bottom-up
        function calcWidth(node) {
            if (!node) return 0;
            const kids = (node.children || []).filter(Boolean);
            if (kids.length === 0) {
                node._w = NODE_W;
            } else {
                kids.forEach(calcWidth);
                const total = kids.reduce((s, k) => s + k._w, 0) + H_GAP * (kids.length - 1);
                node._w = Math.max(NODE_W, total);
            }
        }

        // 2. Assign x/y positions top-down
        function assignPos(node, x, y) {
            if (!node) return;
            node._x = x + node._w / 2;
            node._y = y;
            const kids = (node.children || []).filter(Boolean);
            let cx = x;
            kids.forEach(k => {
                assignPos(k, cx, y + NODE_H + V_GAP);
                cx += k._w + H_GAP;
            });
        }

        // 3. Collect all nodes and edges
        function collect(node, edges, nodes) {
            if (!node) return;
            nodes.push(node);
            (node.children || []).filter(Boolean).forEach(k => {
                edges.push({ x1: node._x, y1: node._y + NODE_H,
                             x2: k._x,   y2: k._y });
                collect(k, edges, nodes);
            });
        }

        // 4. Compute total canvas size
        function maxXY(node, acc) {
            if (!node) return acc;
            acc.maxX = Math.max(acc.maxX, node._x + NODE_W / 2);
            acc.maxY = Math.max(acc.maxY, node._y + NODE_H);
            (node.children || []).filter(Boolean).forEach(k => maxXY(k, acc));
            return acc;
        }

        calcWidth(root);
        assignPos(root, 10, 10);

        const edges = [], nodes = [];
        collect(root, edges, nodes);
        const { maxX, maxY } = maxXY(root, { maxX: 0, maxY: 0 });

        const svgW = maxX + 20;
        const svgH = maxY + 20;

        const NS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(NS, 'svg');
        svg.setAttribute('width',  svgW);
        svg.setAttribute('height', svgH);
        svg.setAttribute('class',  'ast-svg');

        // Draw edges
        edges.forEach(e => {
            const line = document.createElementNS(NS, 'line');
            line.setAttribute('x1', e.x1); line.setAttribute('y1', e.y1);
            line.setAttribute('x2', e.x2); line.setAttribute('y2', e.y2);
            line.setAttribute('class', 'ast-edge');
            svg.appendChild(line);
        });

        // Draw nodes
        nodes.forEach(n => {
            const g = document.createElementNS(NS, 'g');

            const rect = document.createElementNS(NS, 'rect');
            rect.setAttribute('x',      n._x - NODE_W / 2);
            rect.setAttribute('y',      n._y);
            rect.setAttribute('width',  NODE_W);
            rect.setAttribute('height', NODE_H);
            rect.setAttribute('rx',     6);
            rect.setAttribute('ry',     6);
            rect.setAttribute('class',  'ast-node');
            g.appendChild(rect);

            const text = document.createElementNS(NS, 'text');
            text.setAttribute('x',            n._x);
            text.setAttribute('y',            n._y + NODE_H / 2 + FONT_SIZE / 3);
            text.setAttribute('text-anchor',   'middle');
            text.setAttribute('font-size',     FONT_SIZE);
            text.setAttribute('class',         'ast-label');
            // Truncate long labels
            const label = (n.label || '').length > 22
                ? (n.label || '').slice(0, 20) + '…'
                : (n.label || '');
            text.textContent = label;
            g.appendChild(text);

            svg.appendChild(g);
        });

        return svg;
    }
});
