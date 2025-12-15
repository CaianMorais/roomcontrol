import Inputmask from "https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.9/inputmask.es6.min.js";

Inputmask({
    alias: "decimal",
    radixPoint: ",",
    groupSeparator: ".",
    prefix: 'R$ ',
    digits: 2,
    digitsOptional: false,
    rightAlign: false,
    removeMaskOnSubmit: true,
    unmaskAsNumber: true,
}).mask('#price');

const pathname = window.location.pathname.toLowerCase();
const roomType = document.getElementById("room_type");
const adultsInput = document.getElementById("capacity_adults");
const childrenInput = document.getElementById("capacity_children");
const totalInput = document.getElementById("capacity_total");
totalInput.readOnly = true;

const roomCapacities = {
    "1": [1, 0],
    "2": [1, 1],
    "3": [2, 0],
    "4": [2, 0],
    "5": [1, 2],
    "6": [2, 1],
    "7": [3, 0],
    "8": [2, 1],
};

function updateCapacity() {
    const type = roomType.value;

    if (type === "9") { 
        adultsInput.readOnly = false;
        childrenInput.readOnly = false;
        adultsInput.value = "";
        childrenInput.value = "";
        totalInput.value = "";
    } else if (roomCapacities[type]) {
        const [adults, children] = roomCapacities[type];
        adultsInput.value = adults;
        childrenInput.value = children;
        adultsInput.readOnly = true;
        childrenInput.readOnly = true;
        totalInput.value = adults + children;
    } else {
        adultsInput.value = "";
        childrenInput.value = "";
        totalInput.value = "";
        adultsInput.readOnly = true;
        childrenInput.readOnly = true;
    }
}

function updateTotal() {
    const adults = parseInt(adultsInput.value) || 0;
    const children = parseInt(childrenInput.value) || 0;
    totalInput.value = adults + children;
}

roomType.addEventListener("change", updateCapacity);
adultsInput.addEventListener("input", updateTotal);
childrenInput.addEventListener("input", updateTotal);

// EXECUTA A FUNÇÃO SOMENTE SE FOR O FORM DE CRIAÇÃO
if(pathname.includes('/new/')){
    updateCapacity();
}
