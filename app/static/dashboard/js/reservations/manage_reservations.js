// MASCARA DO INPUT CPF
$("#cpf").inputmask({
    mask: ['999.999.999-99'],
    keepStatic: true,
    rightAlign: false,
    removeMaskOnSubmit: true,
    unmaskAsNumber: true,
});

document.addEventListener("DOMContentLoaded", function () {
    const updateBtn = document.querySelectorAll(".btn-update-reservation");
    const cancelBtn = document.querySelectorAll(".btn-cancel-reservation");

    updateBtn.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.href;

            Swal.fire({
                title: "Atualizar a situação da reserva?",
                text: "Essa ação é irreversível.",
                icon: "question",
                showCancelButton: true,
                confirmButtonColor: "#3085d6",
                cancelButtonColor: "#d33",
                confirmButtonText: "Sim!"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
    cancelBtn.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.href;

            Swal.fire({
                title: "Cancelar esta reserva?",
                text: "Essa ação é irreversível.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#3085d6",
                cancelButtonColor: "#d33",
                confirmButtonText: "Sim!"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});