import React from "react";
import classes from "./Markdown.module.css";

import ReactMarkdown from "react-markdown";

// Defines an image renderer
const imageRenderer = (props) => {
  return <img className={classes.photo} alt={props.alt} src={props.src} />;
};

// Defines a link renderer
const linkRenderer = (props) => {
  return (
    <a href={props.href} target="_blank" rel="noopener noreferrer">
      {props.children}
    </a>
  );
};

// Save the renderers in an object
const renderers = {
  image: imageRenderer,
  link: linkRenderer,
};

// Define the Markdwon component
const markdown = (props) => {
  return (
    <div className={classes.App}>
      <ReactMarkdown source={props.markdown} renderers={ renderers } />
    </div>
  );
};

export default markdown;
