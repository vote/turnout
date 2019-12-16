const path = require("path");

module.exports = {
  entry: "./assets/app.js",
  output: {
    filename: "bundle.js",
    path: path.resolve(__dirname, "dist")
  },
  mode: "development",
  module: {
    rules: [
      {
        test: /\.(scss)$/,
        use: [
          {
            // Adds CSS to the DOM by injecting a `<style>` tag
            loader: "style-loader"
          },
          {
            // Interprets `@import` and `url()` like `import/require()` and will resolve them
            loader: "css-loader"
          },
          {
            // Loader for webpack to process CSS with PostCSS
            loader: "postcss-loader",
            options: {
              plugins: function() {
                return [require("autoprefixer")];
              }
            }
          },
          {
            // Loads a SASS/SCSS file and compiles it to CSS
            loader: "sass-loader"
          }
        ]
      }
    ]
  }
};
