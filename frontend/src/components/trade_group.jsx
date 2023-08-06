import React from 'react';
import { Trade } from './trade'

export function TradeGroup(props) {
  const tradeComponents = props.trades.slice(0,5).map(
    (t) => <Trade trade={t} tradeKey={props.tradeKey} key={t.uid1}></Trade>
  )

  return (
    <div className="tradeGroup">
      TRADE GROUP  <span className="mono">{props.tradeKey}</span>
      {tradeComponents}
    </div>
  );
}
