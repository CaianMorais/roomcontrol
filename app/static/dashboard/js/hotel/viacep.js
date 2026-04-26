import { showAlert } from '../alerts.js';

document.addEventListener('DOMContentLoaded', function () {
    // isola os campos do formulário
    const cepInput = document.getElementById('zip_code');
    const addressInput = document.getElementById('address');
    const cityInput = document.getElementById('city');
    const stateInput = document.getElementById('state');

    // remove caracteres não numéricos do CEP
    const onlyDigits = (s) => (s || '').replace(/\D/g, '');

    // função que busca o endereço pelo CEP
    async function fetchByCep() {
        const digits = onlyDigits(cepInput.value);
        if (digits.length !== 8) return;

        // busca o endereço pelo CEP na API ViaCEP
        try {
            const res = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
            const data = await res.json();
            if (data.erro) {
                showAlert('Erro', 'CEP não encontrado.', 'error', true, 2000)
                    .then(() => cepInput.value = '');
                return;
            }

            // insere os dados nos campos do formulário
            if (data.logradouro) addressInput.value = data.logradouro;
            if (data.localidade) cityInput.value = data.localidade;
            if (data.uf) stateInput.value = data.uf.toUpperCase();
        } catch (e) {
            showAlert('Erro', 'Erro ao consultar CEP.', 'error', true, 2000)
                .then(() => {
                    cepInput.value = '';
                });
        }
    }

    cepInput.addEventListener('input', () => {
        if (onlyDigits(cepInput.value).length === 8) fetchByCep();
    });
});
