import axios from 'axios'
import React from 'react';
import { TradeGroup } from './trade_group'

export class Trades extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      groups: []
    }
  }

  componentDidMount () {
    const httpClient = axios.create();
    httpClient.defaults.timeout = 99999;
    httpClient.get('http://127.0.0.1:5000/goodtrades', {
      params: {
      }
    }).then((response) => {
      this.setState({
        groups: response.data
      })
    })
    .catch((error) => {
      console.log(error);
    })
  }

  loadError() {
    return (
      <div>
        No profitable trades found, or first loading in progress...
      </div>
    )
  }

  render() {
    const groupComponents = []
    Object.keys(this.state.groups).forEach((key) => {
      groupComponents.push(
        <TradeGroup 
          trades={this.state.groups[key]}
          tradeKey={key}
          key={key} 
        />
      )
    })

    return (
      <div>
        {groupComponents.length > 0 ? groupComponents : this.loadError()}
      </div>
    )
  }
}



