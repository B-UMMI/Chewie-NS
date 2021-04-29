import React, { Component } from "react";
import {
  Route,
  Switch,
  withRouter,
  Redirect,
  Link,
  useRouteMatch,
} from "react-router-dom";
import { connect } from "react-redux";

// Chewie local components imports
import Aux from "./hoc/Aux/Aux";
import Stats from "./containers/Stats/Stats";
import About from "./containers/About/About";
import Locus from "./containers/Locus/Locus";
import Chewie from "./containers/Chewie/Chewie";
import Schema from "./containers/Schema/Schema";
import Logout from "./containers/Auth/Logout/Logout";
import Species from "./containers/Species/Species";
import MuiLogin from "./containers/Auth/MuiLogin/MuiLogin";
import Sequences from "./containers/Sequences/Sequences";
import MuiRegister from "./containers/Auth/MuiRegister/MuiRegister";
import MuiSideDrawer from "./components/Navigation/MuiSideDrawer/MuiSideDrawer";
import * as actions from "./store/actions/index";

// Material Ui Components
import MuiLink from "@material-ui/core/Link";
import Breadcrumbs from "@material-ui/core/Breadcrumbs";

// Determine URL matches for Breadcrumb generation
function SimpleBreadcrumbs() {
  const aboutMatches = useRouteMatch("/about");
  const statsMatches = useRouteMatch("/stats");
  const sequencesMatches = useRouteMatch("/sequences");
  const speciesIdMatches = useRouteMatch("/species/:species_id");
  const schemasIdMatches = useRouteMatch(
    "/species/:species_id/schemas/:schema_id"
  );
  const locusIdMatches = useRouteMatch(
    "/species/:species_id/schemas/:schema_id/locus/:locus_id"
  );

  const styles = {
    breadcrumb: {
      color: "#bb7944",
    },
  };

  const spd = JSON.parse(localStorage.getItem("speciesD"));
  const schemaName = localStorage.getItem("schemaName");

  // Breadcrumbs generation
  return (
    <>
      <Breadcrumbs aria-label="breadcrumb">
        {aboutMatches && (
          <div>
            <MuiLink component={Link} to="/about" style={styles.breadcrumb}>
              About
            </MuiLink>
          </div>
        )}
        {sequencesMatches && (
          <MuiLink component={Link} to="/sequences" style={styles.breadcrumb}>
            Search
          </MuiLink>
        )}
        {statsMatches && (
          <MuiLink component={Link} to="/stats" style={styles.breadcrumb}>
            Schemas
          </MuiLink>
        )}
        {speciesIdMatches && (
          <MuiLink
            component={Link}
            to={`/species/${speciesIdMatches.params.species_id}`}
            style={styles.breadcrumb}
          >
            <i>{spd[speciesIdMatches.params.species_id]}</i>
          </MuiLink>
        )}
        {schemasIdMatches && (
          <MuiLink
            component={Link}
            to={`/species/${schemasIdMatches.params.species_id}/schemas/${schemasIdMatches.params.schema_id}`}
            style={styles.breadcrumb}
          >
            {schemaName}
          </MuiLink>
        )}
        {locusIdMatches && (
          <MuiLink
            component={Link}
            to={`/schemas/${locusIdMatches.params.schema_id}/locus/${locusIdMatches.params.locus_id}`}
            style={styles.breadcrumb}
          >
            Locus {locusIdMatches.params.locus_id}
          </MuiLink>
        )}
      </Breadcrumbs>
    </>
  );
}

class App extends Component {
  componentDidMount() {
    this.props.onTryAutoSignup();
  }

  render() {
    // Define common app routes
    let routes = (
      <Aux>
        <SimpleBreadcrumbs />
        <Switch>
          <Route path="/auth" component={MuiLogin} />
          <Route path="/register" component={MuiRegister} />
          <Route path="/about" component={About} />
          <Route path="/" exact component={Chewie} />
          <Route path="/stats" component={Stats} />
          <Route path="/sequences" component={Sequences} />
          <Route
            path="/species/:species_id/schemas/:schema_id/locus/:locus_id"
            component={Locus}
          />
          <Route
            path="/species/:species_id/schemas/:schema_id"
            component={Schema}
          />
          <Route path="/species/:species_id" component={Species} />
          <Redirect to="/" />
        </Switch>
      </Aux>
    );

    if (this.props.isAuthenticated) {
      // Defines user authenticated routes
      routes = (
        <Switch>
          <Route path="/logout" component={Logout} />
          <Route path="/about" component={About} />
          <Route path="/stats" component={Stats} />
          <Route path="/sequences" component={Sequences} />
          <Route path="/" exact component={Chewie} />
          <Route
            path="/species/:species_id/schemas/:schema_id/locus/:locus_id"
            component={Locus}
          />
          <Route
            path="/species/:species_id/schemas/:schema_id"
            component={Schema}
          />
          <Route path="/species/:species_id" component={Species} />
          <Redirect to="/" />
        </Switch>
      );
    }

    return (
      <div>
        <MuiSideDrawer>{routes}</MuiSideDrawer>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    isAuthenticated: state.auth.token !== null,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onTryAutoSignup: () => dispatch(actions.authCheckState()),
  };
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(App));
