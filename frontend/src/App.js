import './App.css';

import { HashRouter as Router, Route, Switch } from 'react-router-dom';import './index.css';

import { Trades } from './components/trades';
import { GroupHome } from './groupdetail/grouphome';

function App() {
  return (
    <div className="App">
      <Router>
        <Switch>
          <Route path="/grouphome" component={GroupHome} />
          <Route exact path="/" component={Trades} />
        </Switch>
      </Router>
    </div>
  );
}

export default App;
