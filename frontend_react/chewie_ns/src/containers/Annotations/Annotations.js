import React, { Component } from "react";
import { connect } from "react-redux";

import axios from "../../axios-backend";
import withErrorHandler from "../../hoc/withErrorHandler/withErrorHandler";
import Aux from "../../hoc/Aux/Aux"
import * as actions from "../../store/actions/index";

// Material-UI components
import CircularProgress from "@material-ui/core/CircularProgress";
import Typography from "@material-ui/core/Typography";
import Box from "@material-ui/core/Box";

// Material-UI Datatables
import MUIDataTable from "mui-datatables";

class Annotations extends Component {
  componentDidMount() {
    this.props.onFetchAnnotations();
  }

  render() {
    let annotations = <CircularProgress />;
    if (!this.props.loading) {
      const columns = [
        {
          name: "uniprot_label",
          label: "Uniprot Label",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              };
            }
          }
        },
        {
          name: "uniprot_uri",
          label: "Uniprot URI",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              };
            },
            customBodyRender: (value, tableMeta, updateValue) => {
              return (
                <a href={value} target="_blank" rel="noopener noreferrer">
                  {value}
                </a>
              );
            }
          }
        },
        {
          name: "species",
          label: "Species",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              };
            },
            customBodyRender: (value, tableMeta, updateValue) => (
              <Aux>
                <Typography component="div">
                  <Box
                    display="inline"
                    fontStyle="italic"
                    m={1}
                  >
                    {value}
                  </Box>
                </Typography>
              </Aux>
            )
          }
        },
        // {
        //   name: "schema",
        //   label: "Schema ID",
        //   options: {
        //     filter: true,
        //     sort: true,
        //     display: true,
        //     setCellHeaderProps: value => {
        //       return {
        //         style: {
        //           fontWeight: "bold"
        //         }
        //       };
        //     }
        //   }
        // },
        {
          name: "locus",
          label: "Locus ID",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              };
            }
          }
        },
        {
          name: "locus_name",
          label: "Locus Label",
          options: {
            filter: true,
            sort: true,
            display: true,
            setCellHeaderProps: value => {
              return {
                style: {
                  fontWeight: "bold"
                }
              }
            }
          }
        }
      ];

      const options = {
        textLabels: {
          body: {
            noMatch: <CircularProgress />
          }
        },
        responsive: "scrollMaxHeight",
        selectableRowsHeader: false,
        selectableRows: "none",
        selectableRowsOnClick: false,
        print: false,
        download: true,
        filter: true,
        filterType: "multiselect",
        search: true,
        viewColumns: true,
        pagination: true
      };

      annotations = (
        <MUIDataTable
          title={"Annotations"}
          data={this.props.annotations}
          columns={columns}
          options={options}
        />
      );
    }
    return <div>{annotations}</div>;
  }
}

const mapStateToProps = state => {
  return {
    annotations: state.annotations.annotations,
    loading: state.annotations.loading,
    error: state.annotations.error
    // token: state.auth.token
  };
};

const mapDispatchToProps = dispatch => {
  return {
    onFetchAnnotations: () => dispatch(actions.fetchAnnotations())
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withErrorHandler(Annotations, axios));
