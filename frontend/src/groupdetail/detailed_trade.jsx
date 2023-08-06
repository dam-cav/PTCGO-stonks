import axios from 'axios'

function acceptTrade (uid) {
  axios.post(`http://127.0.0.1:5000/accepttrade?uid=${uid}`, {
  }).then((response) => {
    console.log(response)
  })
  .catch((error) => {
    console.log(error);
  })
}

function dateToString(date) {
  const day = date.getDate();
  const month = date.getMonth()+1;
  const year = date.getFullYear();

  const hours = date.getHours();
  const minutes = "0" + date.getMinutes();
  const seconds = "0" + date.getSeconds();

  const formattedTime = `${day}/${month}/${year} ${hours}:${minutes.substr(-2)}:${seconds.substr(-2)}`;
  return formattedTime;
}

export function DetailedTrade(props) {
  const formattedCreation = dateToString(new Date(props.trade.creation))
  const formattedInspection = dateToString(new Date(props.trade.inspection))
  const formattedExpiration = dateToString(new Date(props.trade.expiration))

  return (
    <div className="trade">
      <b>Trade</b>&nbsp;
      <span className="mono">{props.trade.uid}</span>
      <span className="confirm">
        <span className="mono">{formattedCreation}</span>
        &nbsp;&#8594;&nbsp;
        <span className="mono">{formattedInspection}</span>
        &nbsp;&#8594;&nbsp;
        <span className="mono">{formattedExpiration}</span>
      </span>
      <hr/>

      <div
        onClick={() => {acceptTrade(props.trade.uid)}}
        className='confirm accept'
      > ! </div>

      <div className="flex">
        <div className="left">
          <b>{props.trade.given.card_name}</b>
          <br/>
          <span className="mono">{props.trade.given.archetype_id}</span>
          <br/>
          {props.trade.given.set_tag} {props.trade.given.card_number}
          <br/>
          Quantity: {props.trade.given.quantity} {props.trade.given.extra_objects ? '+ BONUS' : null}
        </div>
        <div className="right">
          <b>{props.trade.requested.card_name}</b>
          <br/>
          <span className="mono">{props.trade.requested.archetype_id}</span>
          <br/>
          {props.trade.requested.set_tag} {props.trade.requested.card_number}
          <br/><br/>
          Quantity: {props.trade.requested.quantity}
        </div>
      </div>
    </div>
  );
}
