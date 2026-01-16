const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

app.get("/sample-app", (_req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>QA Demo Sample App</title>
      </head>
      <body>
        <h1>QA Demo Sample App</h1>
        <p>This is a minimal deterministic sample app used for automated QA demo flows.</p>
        <a href="/sample-app/login">Go to login</a>
      </body>
    </html>
  `);
});

app.get("/sample-app/login", (_req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Sample Login</title>
      </head>
      <body>
        <h1>Login</h1>
        <form>
          <label for="username">Username</label>
          <input id="username" name="username" type="text" />
          <label for="password">Password</label>
          <input id="password" name="password" type="password" />
          <button id="login" type="button">Login</button>
        </form>
        <script>
          document.getElementById("login").addEventListener("click", function () {
            // Deterministic, read-only "login" that just updates text on the page.
            const msg = document.createElement("h2");
            msg.textContent = "Welcome";
            document.body.appendChild(msg);
          });
        </script>
      </body>
    </html>
  `);
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Sample app listening on port ${PORT}`);
});
