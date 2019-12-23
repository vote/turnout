import "bootstrap";
import "jquery";
import "popper.js";
import "./scss/app.scss";

$(document).ready(function() {
  $(".dropdown-expand-link").click(function(e) {
    e.preventDefault();
  });
});
