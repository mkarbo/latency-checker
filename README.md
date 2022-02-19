After several months of network connection being wonky, I made this to gather some data to display to my ISP.

Tech:
- Influxdb, a time series database
- grafana, a dashboard/BI tool
- chronograf, admin UI
- python-pinger, a simple homemade smack-together for pinging google and cloudflare dns servers (`8.8.8.8` and `1.1.1.1`)

To use, simple run:
`
sudo docker-compose build
sudo docker-compose up -d
`

And go to either `http://localhost:8086` (fluxdb UI) or `http://localhost:3000`.

I might convert some of these into kubernetes manifests later or address ssl/https for python ping service (pretty sure it will break as is, but so far it just runs on a local Intel NUC)
