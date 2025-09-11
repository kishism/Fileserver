# Hypermedia-Driven FTP Server

A simple FTP-like server built with **Flask** that serves directory and file structures as **hypermedia HTML**.  

Instead of just exposing raw data, every response includes **hypermedia controls** (links, headers, and allowed methods) so both humans and automated clients can explore and interact with the system.

In a way, this project can be seen as an attempt to faithfully follow Fielding's original definition of REST, and proper use of HTTP verbs.

## How Hypermedia Works

This project is designed around the idea that every HTTP response should guide the client on what it can do next. Instead of just returning raw HTML or JSON, each response includes **hypermedia controls**: links and headers that describe available actions. 

Hypermedia is the idea that information on the web should not only provide **data**, but also describe the **actions and navigation paths** available from that point. It extends the concept of “hypertext” (like links in an HTML page) into a broader system of **controls, affordances, and machine-readable guidance**.

{###}

Bozo Contributors

<div>
  <div>
  <a href="https://github.com/kishism">
    <img src="https://avatars.githubusercontent.com/u/157962042?v=4" width="100" style="margin: 0 10px;" alt="Kishi"/> 
  </a>

  <a href="https://github.com/DazeAkaRiku">
    <img src="https://avatars.githubusercontent.com/u/121934782?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>

  <a href="https://github.com/Janica-Max">
    <img src="https://avatars.githubusercontent.com/u/218932649?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>

  <a href="https://github.com/Yokkathsoe">
    <img src="https://avatars.githubusercontent.com/u/159621518?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>

  <a href="https://github.com/saipanesaing">
    <img src="https://avatars.githubusercontent.com/u/159633689?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>
  
</div>