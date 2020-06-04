import React from "react";
import classes from "./Markdown.module.css";

import ReactMarkdown from "react-markdown";

const imageRenderer = (props) => {
  return <img className={classes.photo} alt={props.alt} src={props.src} />;
};

const linkRenderer = (props) => {
  return (
    <a href={props.href} target={"_blank"} rel="noopener noreferrer">
      {props.children}
    </a>
  );
};

const renderers = {
  image: imageRenderer,
  link: linkRenderer,
};

const markdown = (props) => {
  return (
    <div className={classes.App}>
      <ReactMarkdown source={props.markdown} renderers={{ renderers }} />
    </div>
  );
};

export default markdown;
