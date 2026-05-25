// ==UserScript==
// @name         Fervo — Impressão Automática de Etiquetas
// @namespace    https://lojas.fervo.com.br
// @version      1.0.0
// @description  Imprime etiqueta de envio automaticamente ao concluir embalagem no Olist/Tiny
// @author       Fervo Expedição
// @match        https://erp.tiny.com.br/*
// @match        https://app.tiny.com.br/*
// @grant        none
// @updateURL    https://raw.githubusercontent.com/contejao/fervo-expedicao/main/tampermonkey/fervo-expedicao.user.js
// @downloadURL  https://raw.githubusercontent.com/contejao/fervo-expedicao/main/tampermonkey/fervo-expedicao.user.js
// ==/UserScript==

(function () {
    'use strict';

    const LOG_PREFIX = '[Fervo Expedição]';

    function log(msg) {
        console.log(`${LOG_PREFIX} ${msg}`);
    }

    // Encontra e clica no botão de etiqueta de envio dentro do elemento do toast
    function clicarEtiqueta(toastEl) {
        // Aguarda 400ms para garantir que os event handlers do React estão conectados
        setTimeout(() => {
            const botoes = toastEl.querySelectorAll('button, a[role="button"], span[role="button"]');
            let alvo = null;

            for (const btn of botoes) {
                const texto = btn.textContent.toLowerCase().trim();
                const ehEtiqueta = texto.includes('etiqueta');
                const naoEhVolumes = !texto.includes('volume');
                const naoEhDanfe = !texto.includes('danfe');

                if (ehEtiqueta && naoEhVolumes && naoEhDanfe) {
                    alvo = btn;
                    break;
                }
            }

            if (alvo) {
                log(`Embalagem concluída — clicando em: "${alvo.textContent.trim()}"`);
                alvo.click();
            } else {
                log('Toast de conclusão detectado mas botão de etiqueta não encontrado. Verifique o console.');
                log('Botões disponíveis: ' + [...botoes].map(b => b.textContent.trim()).join(' | '));
            }
        }, 400);
    }

    // Verifica se um nó recém-adicionado é o toast de conclusão de embalagem
    function verificarToast(node) {
        if (node.nodeType !== 1) return;

        const texto = node.textContent || '';

        if (texto.includes('concluída') || texto.includes('concluida')) {
            // Verifica se é o toast de embalagem de produtos (não outro toast qualquer)
            if (texto.toLowerCase().includes('embalag') || texto.toLowerCase().includes('nota')) {
                log(`Toast detectado: "${texto.substring(0, 80).trim()}..."`);
                clicarEtiqueta(node);
                return;
            }
        }

        // Verifica descendentes (o toast pode ser adicionado como container pai)
        const descendentes = node.querySelectorAll('*');
        for (const el of descendentes) {
            const t = el.textContent || '';
            if ((t.includes('concluída') || t.includes('concluida')) && t.toLowerCase().includes('embalag')) {
                log(`Toast detectado em descendente: "${t.substring(0, 80).trim()}..."`);
                clicarEtiqueta(el.closest('[class*="toast"], [class*="modal"], [class*="notification"], [class*="alert"]') || el.parentElement || el);
                return;
            }
        }
    }

    // MutationObserver no body inteiro para capturar toasts injetados dinamicamente
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                verificarToast(node);
            }
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    log('Ativo — monitorando conclusão de embalagem...');
})();
