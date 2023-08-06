export function Trade(props) {
  return (
    <div className="trade">
      <span className="mono">{props.trade.uid1}</span>
      <a
        href={`${window.location.pathname}#/grouphome?duid1=${props.trade.duid1}&duid2=${props.tradeKey}`}
        target="_blank"
        className='confirm forward'
      > &gt; </a>

      <div className="flex trade-values">
        <div className="left">
          <span className="gain">ESTIMATED EARNINGS</span>
          {props.trade.gain}
          {props.trade.bonus1 ? ' + B1' : ''}
          {props.trade.bonus2 ? ' + B2' : ''}
        </div>

        <div className="right">
          <span className="risk">COMMITMENT</span>
          {props.trade.risk}
        </div>
      </div>
    </div>
  );
}
