// EveCompiler IDE Frontend JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const sourceCodeEl = document.getElementById('sourceCode');
    const compileBtn = document.getElementById('compileBtn');
    const clearBtn = document.getElementById('clearBtn');
    const sampleBtn = document.getElementById('sampleBtn');
    const sampleModal = document.getElementById('sampleModal');
    const closeBtn = document.querySelector('.close-btn');
    const statusContainer = document.getElementById('statusContainer');

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
                displayOutput(data);
            } else {
                showStatus(`❌ ${data.error}`, 'error');
                document.getElementById('outputContent').innerHTML = 
                    `<div class="error-message"><strong>Compilation Error:</strong><br>${escapeHtml(data.error)}</div>`;
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
});
