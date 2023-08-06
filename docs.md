## How to make client talk to your fake server

dwd\core\wargServer.connectors\ThrottledGatewayConnector

```
// line 49
// Token: 0x06001D6A RID: 7530 RVA: 0x00070D8C File Offset: 0x0006EF8C
public ThrottledGatewayConnector(string hostname, int port, bool useSSL, string clientVersion, IDictionary<string, string> clientParameters, IMessageToCommandFactory messageFactory, WargSocketLogConfiguration logConfiguration = null)
{
	this.hostname = hostname; // set 'localhost'
	this.port = port;
	this.clientVersion = clientVersion;
	this.clientParameters = (clientParameters ?? new DWDSystemInfo());
	this.messageFactory = messageFactory;
	this.logConfiguration = logConfiguration;
	this.socketOptions = new SocketOptions
	{
		UseSSL = useSSL
	};
}
```

```
// in C:\Windows\System32\drivers\etc\hosts
127.0.0.1 localhost-connection-78-9.direwolfdigital.com
```

## Obtain collection data to fill the db

pie-src\-\CollectionListViewDataSource.cs

```
// riga 51

using dwd.core.data.composition; // must be added!!!!

// Token: 0x0200037E RID: 894
public partial class CollectionListViewDataSource : UIListDataSource
{
	// Token: 0x060010BE RID: 4286 RVA: 0x0004280C File Offset: 0x00040A0C
	public void setData(string filterType, IList<ArchetypeComponent> newData, bool resetScroll)
	{
		if (resetScroll)
		{
			this.uiList.scrollPosition = 0f;
		}
		this.currentFilter = filterType;
		this.data = (this.get_SortInvert() ? this.invertData(newData) : newData);
		this.uiList.reloadData(false);
		IEnumerator<DataComponent> a;
		try
		{
			for (int i = 0; i < 999999; i++)
			{
				Console.WriteLine("Card");
				Console.WriteLine(newData[i].ArchetypeID);
				a = newData[i].get_Composition().GetEnumerator();
				a.MoveNext();
				Console.WriteLine(((IEnumerator<DataComponent>)a).Current); // archetypeid info
				a.MoveNext();
				Console.WriteLine(((IEnumerator<DataComponent>)a).Current); // name
				a.MoveNext();
				Console.WriteLine(((IEnumerator<DataComponent>)a).Current); // set
				a.MoveNext();
				a.MoveNext();
				a.MoveNext(); // OK for pokemon, remove for trainer and energy
				Console.WriteLine(((IEnumerator<DataComponent>)a).Current); // various foilness
			}
		}
		catch (ArgumentOutOfRangeException)
		{
		}
	}
}
```