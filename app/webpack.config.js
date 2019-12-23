const path = require("path");
const LiveReloadPlugin = require("webpack-livereload-plugin");

module.exports = {
  entry: "./assets/app.js",
  output: {
    filename: "bundle.js",
    path: path.resolve(__dirname, "dist"),
    publicPath: "/static"
  },
  plugins: [
    new LiveReloadPlugin({
      port: 35729,
      hostname: "localhost"
    })
  ],
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
      },
      {
        test: /\.(eot|ttf|woff|woff2)(\??\#?v=[.0-9]+)?$/,
        loader: "file-loader?name=/fonts/[contenthash].[name].[ext]"
      },
      {
        test: /\.(png|svg|jpeg|jpg|ico)(\??\#?v=[.0-9]+)?$/,
        loader: "file-loader?name=/images/[contenthash].[name].[ext]"
      }
    ]
  }
};
