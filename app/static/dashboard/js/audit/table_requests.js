$('#audit').DataTable( {
    destroy :true,
    responsive: true,
    language: {
        url: 'https://cdn.datatables.net/plug-ins/2.3.5/i18n/pt-BR.json',
    },
    order: [[
        0, 'desc'
    ]],
    layout: {
        topStart: 'info',
        topEnd: 'search',
        bottom: 'paging',
        bottomStart: null,
        bottomEnd: null
    }
})