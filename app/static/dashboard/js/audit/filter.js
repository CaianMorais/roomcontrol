import { showAlert } from "../alerts.js";

const beforeInput = document.getElementById('before');
const afterInput = document.getElementById('after');
const form = document.getElementById('audit_filter');

form.addEventListener("submit", event => {
    const beforeDate = beforeInput.value;
    const afterDate = afterInput.value;

    if (!beforeDate || !afterDate) return;

    if (afterDate > beforeDate) {
        event.preventDefault();
        showAlert("Opa...", "As datas são incompatíveis, tente novamente", "error", true, 2000);
        beforeInput.value = ''; afterInput.value = '';
        return;
    }
});
