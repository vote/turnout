import SimpleMDE from 'simplemde';

import $ from 'jquery';

$(document).ready(() => {
  $("textarea.markdown-preview").each((i, el) => {
    new SimpleMDE({ element: el });
  });
});
