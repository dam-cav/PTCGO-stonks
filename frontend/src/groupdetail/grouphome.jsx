import axios from 'axios'
import React from 'react';

import { DetailedTrade } from './detailed_trade';

export class GroupHome extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      firstTrade: null,
      secondTrande: null,
      finalTrades: [],
      failureTrades: []
    }
  }

  
  componentDidMount () {
    const search =  this.props.location.search;
    const duid1 = new URLSearchParams(search).get('duid1');
    const duid2 = new URLSearchParams(search).get('duid2');

    if(duid1 && duid2) {
      axios.get(`http://127.0.0.1:5000/trade?duid=${duid1}`, {
        params: {
        }
      }).then((response) => {
        this.setState({
          firstTrade: response.data
        })
        this.searchGainForArchetypeId(response.data.given.archetype_id, 'failure')
      })
      .catch((error) => {
        console.log(error);
      })

      axios.get(`http://127.0.0.1:5000/trade?duid=${duid2}`, {
        params: {
        }
      }).then((response) => {
        this.setState({
          secondTrade: response.data
        })
        this.searchGainForArchetypeId(response.data.given.archetype_id, 'final')
      })
      .catch((error) => {
        console.log(error);
      })
    }
  }

  searchGainForArchetypeId (archetype_id, situation) {
    axios.get(`http://127.0.0.1:5000/tradefor?archetype_id=${archetype_id}`, {
      params: {
      }
    }).then((response) => {
      switch(situation) {
        case 'failure':
          this.setState({
            failureTrades: response.data
          })
          break;
        case 'final':
          this.setState({
            finalTrades: response.data
          })
          break;
      }

    })
    .catch((error) => {
      console.log(error);
    })
  }

  render() {
    const detailedTrades = []
    const back = `${window.location.pathname}#/`
    
    if (this.state.firstTrade && this.state.secondTrade) {
      detailedTrades.push(<DetailedTrade trade={this.state.firstTrade} key={this.state.firstTrade.uid} />)
      detailedTrades.push(<DetailedTrade trade={this.state.secondTrade} key={this.state.secondTrade.uid} />)
    }

    const finalTrades = this.state.finalTrades.map(
      (trade) => <DetailedTrade trade={trade} key={trade.uid} />
    )

    const failureTrades = this.state.failureTrades.map(
      (trade) => <DetailedTrade trade={trade} key={trade.uid} />
    )

    return (
      <>
        <a href={back} className='back'>&lt;</a>

        <h2>Gain trades</h2>
        {detailedTrades}
        <br/>

        <h2>Pack recovery trades</h2>
        {finalTrades}
        <br/>

        <h2>Failure recovery trades</h2>
        {failureTrades}
      </>
    )
  }
}
