import React, { Component } from "react";
import {
  Route,
  Switch,
  withRouter,
  Redirect,
  Link,
  useRouteMatch
} from "react-router-dom";
import { connect } from "react-redux";

// Chewie Components
import Aux from "./hoc/Aux/Aux";
import Layout from "./hoc/Layout/Layout";
import Chewie from "./containers/Chewie/Chewie";
import Auth from "./containers/Auth/Auth";
import Logout from "./containers/Auth/Logout/Logout";
import Stats from "./containers/Stats/Stats";
import Species from "./containers/Species/Species";
import Schema from "./containers/Schema/Schema";
import Locus from "./containers/Locus/Locus";
import Annotations from "./containers/Annotations/Annotations";
import * as actions from "./store/actions/index";

// Material Ui Components
import Breadcrumbs from "@material-ui/core/Breadcrumbs";
// import Typography from "@material-ui/core/Typography";
// import Link from "@material-ui/core/Link";
import MuiLink from '@material-ui/core/Link';

function SimpleBreadcrumbs() {
  const homeMatches = useRouteMatch("/");
  const statsMatches = useRouteMatch("/stats");
  const annotationMatches = useRouteMatch("/annotations");
  const speciesIdMatches = useRouteMatch("/species/:species_id");
  const schemasIdMatches = useRouteMatch("/species/:species_id/schemas/:schema_id")
  const locusIdMatches = useRouteMatch("/species/:species_id/schemas/:schema_id/locus/:locus_id");
  return (
    <>
      <Breadcrumbs>
        {homeMatches && (
          <MuiLink component={Link} to="/">
            Home
          </MuiLink>
        )}
        {statsMatches && (
          <MuiLink component={Link} to="/stats">
            Schemas
          </MuiLink>
        )}
        {annotationMatches && (
          <MuiLink component={Link} to="/annotations">
            Annotations
          </MuiLink>
        )}
        {speciesIdMatches && (
          <MuiLink component={Link} to={`/species/${speciesIdMatches.params.species_id}`}>
            Species {speciesIdMatches.params.species_id}
          </MuiLink>
        )}
        {schemasIdMatches && (
          <MuiLink component={Link} to={`/species/${schemasIdMatches.params.species_id}/schemas/${schemasIdMatches.params.schema_id}`}>
            Schema {schemasIdMatches.params.schema_id}
          </MuiLink>
        )}
        {locusIdMatches && (
          <MuiLink
            component={Link}
            to={`/schema/${locusIdMatches.params.schema_id}/${
              locusIdMatches.params.locus_id}`}
          >
            Locus {locusIdMatches.params.locus_id}
          </MuiLink>
        )}
      </Breadcrumbs>
    </>
  )
}

class App extends Component {
  componentDidMount() {
    this.props.onTryAutoSignup();
  }

  render() {
    // const breadcrumbNameMap = {
    //   "/stats": "Schemas",
    //   "/annotations": "Annotations"
    //   // "/users/:id": ":id",
    //   // "/users/:id/detail": "Details"
    // };

    // const LinkRouter = props => <Link {...props} component={RouterLink} />;

    // const breadcrumbs = () => (
    //   <MemoryRouter initialEntries={["/stats"]} initialIndex={0}>
    //     <div style={{display: 'flex', flexDirection: 'column', width: 360}}>
    //       <Route>
    //         {({ location }) => {
    //           const pathnames = location.pathname.split('/').filter(x => x);

    //           return (
    //             <Breadcrumbs aria-label="breadcrumb">
    //               <LinkRouter color="inherit" to="/">
    //                 Home
    //               </LinkRouter>
    //               {pathnames.map((value, index) => {
    //                 const last = index === pathnames.length - 1;
    //                 const to = `/${pathnames.slice(0, index + 1).join('/')}`;

    //                 return last ? (
    //                   <Typography color="textPrimary" key={to}>
    //                     {breadcrumbNameMap[to]}
    //                   </Typography>
    //                 ) : (
    //                   <LinkRouter color="inherit" to={to} key={to}>
    //                     {breadcrumbNameMap[to]}
    //                   </LinkRouter>
    //                 )
    //               })}
    //             </Breadcrumbs>
    //           )
    //         }}
    //       </Route>
    //     </div>
    //   </MemoryRouter>
    // )

    let routes = (
      <Aux>
        <SimpleBreadcrumbs />
        <Switch>

          <Route path="/auth" component={Auth} />
          <Route path="/" exact component={Chewie} />
          <Route path="/stats" component={Stats} />
          <Route path="/annotations" component={Annotations} />
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
      routes = (
        <Switch>
          <Route path="/logout" component={Logout} />
          <Route path="/stats" component={Stats} />
          <Route path="/" exact component={Chewie} />
          <Redirect to="/" />
        </Switch>
      );
    }

    return (
      <div>
        <Layout>{routes}</Layout>
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    isAuthenticated: state.auth.token !== null
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onTryAutoSignup: () => dispatch(actions.authCheckState())
  };
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(App));
