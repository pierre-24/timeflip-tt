"use strict";

function setup_modal(class_name, modal, dataset_to_input) {
     Array.from(document.getElementsByClassName(class_name)).forEach(e => {
         e.addEventListener('click', () => {
             // set values
             for (const [k, v] of Object.entries(dataset_to_input)) {
                 let $elm = document.getElementById(k);

                 if (['INPUT', 'SELECT'].includes($elm.tagName))
                     $elm.value = e.dataset[v];
                 else
                     $elm.innerHTML = e.dataset[v];
             }

             // show modal
             $('#' + modal).modal('show');
         });
     });
}

function setup_modals(lst) {
    lst.forEach(e => {
        setup_modal(e.class_name, e.modal, e.dataset_to_input);
    });
}