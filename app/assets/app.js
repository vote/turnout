import "bootstrap";
import $ from "jquery";
import "popper.js";
import "./scss/app.scss";
import "./markdown";
import 'datatables.net-bs4';

$(document).ready(function() {
  $(".dropdown-expand-link").click(function(e) {
    e.preventDefault();
  });

  $(".esign-regions-datatable").DataTable({
    paging: false,
    info: false,
    columnDefs: [
      { type: 'string' },
      { type: 'string' },
      { type: 'num' },
      { type: 'num' },
      { type: 'num' },
      { type: 'num' },
      { type: 'string' }
    ]
  });
});
