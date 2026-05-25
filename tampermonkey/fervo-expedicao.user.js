// ==UserScript==
// @name         Fervo — Impressão Automática de Etiquetas
// @namespace    https://lojas.fervo.com.br
// @version      1.1.0
// @description  Imprime etiqueta automaticamente ao concluir embalagem. Força download de etiquetas que abrem em nova aba (ML, TikTok, etc.)
// @author       Fervo Expedição
// @match        https://erp.tiny.com.br/*
// @match        https://app.tiny.com.br/*
// @grant        GM_download
// @updateURL    https://raw.githubusercontent.com/contejao/fervo-expedicao/main/tampermonkey/fervo-expedicao.user.js
// @downloadURL  https://raw.githubusercontent.com/contejao/fervo-expedicao/main/tampermonkey/fervo-expedicao.user.js
// ==/UserScript==

(function () {
    'use strict';

    const LOG = '[Fervo Expedição]';

    // Flag ativa por 5s após clicar o botão de etiqueta
    // Garante que só interceptamos o window.open gerado pelo nosso clique
    let _interceptarProximoOpen = false;
    let _timerIntercept = null;

    function log(msg) {
        console.log(`${LOG} ${msg}`);
    }

    // --- Interceptação de window.open ---
    // Quando o Olist abre etiqueta em nova aba (ML, TikTok, etc.),
    // capturamos a URL e forçamos download para a pasta Downloads.
    const _originalOpen = window.open.bind(window);
    window.open = function (url, ...args) {
        if (_interceptarProximoOpen && url && typeof url === 'string') {
            _interceptarProximoOpen = false;
            clearTimeout(_timerIntercept);
            log(`Interceptando nova aba → forçando download: ${url.substring(0, 80)}`);

            GM_download({
                url: url,
                name: `etiqueta_${Date.now()}.pdf`,
                onerror: function (err) {
                    log(`Falha no download (${err.error}), abrindo aba normalmente`);
                    _originalOpen(url, ...args);
                }
            });

            return null;
        }
        return _originalOpen(url, ...args);
    };

    // --- Clique automático no botão de etiqueta ---
    function clicarEtiqueta(toastEl) {
        setTimeout(() => {
            const botoes = toastEl.querySelectorAll('button, a[role="button"], span[role="button"]');
            let alvo = null;

            for (const btn of botoes) {
                const texto = btn.textContent.toLowerCase().trim();
                if (texto.includes('etiqueta') && !texto.includes('volume') && !texto.includes('danfe')) {
                    alvo = btn;
                    break;
                }
            }

            if (alvo) {
                log(`Embalagem concluída — clicando em: "${alvo.textContent.trim()}"`);

                // Ativa interceptação por 5s para capturar o window.open do botão
                _interceptarProximoOpen = true;
                clearTimeout(_timerIntercept);
                _timerIntercept = setTimeout(() => {
                    _interceptarProximoOpen = false;
                }, 5000);

                alvo.click();
            } else {
                log('Toast detectado mas botão de etiqueta não encontrado.');
                log('Botões: ' + [...botoes].map(b => b.textContent.trim()).join(' | '));
            }
        }, 400);
    }

    // --- MutationObserver: detecta toast de conclusão ---
    function verificarToast(node) {
        if (node.nodeType !== 1) return;

        const texto = node.textContent || '';
        if ((texto.includes('concluída') || texto.includes('concluida')) &&
            texto.toLowerCase().includes('embalag')) {
            log(`Toast detectado: "${texto.substring(0, 80).trim()}"`);
            clicarEtiqueta(node);
            return;
        }

        for (const el of node.querySelectorAll('*')) {
            const t = el.textContent || '';
            if ((t.includes('concluída') || t.includes('concluida')) &&
                t.toLowerCase().includes('embalag')) {
                const container =
                    el.closest('[class*="toast"], [class*="modal"], [class*="notification"], [class*="alert"]')
                    || el.parentElement
                    || el;
                log(`Toast em descendente: "${t.substring(0, 80).trim()}"`);
                clicarEtiqueta(container);
                return;
            }
        }
    }

    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                verificarToast(node);
            }
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    log('Ativo — monitorando conclusão de embalagem e interceptando novas abas...');
})();
