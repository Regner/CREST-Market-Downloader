import wx
from wx.lib.pubsub import pub
import os
import csv
import requests
import grequests
import time
import locale

__user_agent__ = 'Set this to something...'
__base_url__   = 'http://public-crest-sisi.testeveonline.com'


def make_request(href, accept):
    """ Makes a request to CREST adding the required headers. """

    headers = {
        'Accept'     : accept,
        'User-Agent' : __user_agent__,
    }

    r = requests.get(href, headers=headers)

    # TODO: Add error handling

    return r.json()


def make_multiple_requests(hrefs, accept=None):
    """ Makes multiple async requests using grequests. """

    items   = []
    headers = {
        'Accept'     : accept,
        'User-Agent' : __user_agent__
    }

    rs = (grequests.get(u, headers=headers) for u in hrefs)
    responses = grequests.map(rs)

    # TODO: Add error handling

    for response in responses:
        # TODO: This is specific to a specific type of CREST resource. Fix that.
        items.extend(response.json()['items'])
        response.close()

    return items


# Create a new frame class, derived from the wxPython Frame.
class MarketView(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        panel = wx.Panel(self, -1)

        self.panel       = panel
        self.regionCombo = wx.ComboBox(panel, -1, "", style=wx.CB_READONLY | wx.CB_SORT)
        self.get_region  = wx.Button(panel, id=wx.ID_ANY, label='Dump Region')
        self.save        = wx.Button(panel, id=wx.ID_ANY, label='Export Location')
        self.filter      = wx.Button(panel, id=wx.ID_ANY, label='Filter File')
        self.get_region.Disable()

        self.status_bar=self.CreateStatusBar(style=0)
        self.status_bar.SetFieldsCount(2)
        self.status_bar.SetStatusWidths([-2, -1])
        self.SetStatusText("Please Log in", 0)
        sizer = wx.FlexGridSizer(2, 3, 5, 5)
        sizer.Add(self.regionCombo)
        sizer.Add(self.get_region)
        sizer.Add(self.save)
        sizer.Add(self.filter)
        border = wx.BoxSizer()
        border.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizerAndFit(border)
        self.Fit()
        self.Centre()

    def update_status(self, data, extra1=0):
        self.SetStatusText(data, extra1)
        
    def update_regions(self, regions):
        self.regionCombo.Clear()
        for item in regions['items']:
            self.regionCombo.Append(item['name'], item)
    
    def show_dir(self):
        path = os.getcwd()
        dlg = wx.DirDialog(
            self, "Save file in ...", 
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST | wx.DD_CHANGE_DIR
        )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        return path
    
    def select_filter_file(self):
        file_path = 'nofile'

        wildcard = "CSV (*.csv)|*.csv"
        dlg = wx.FileDialog(
            self, "Select Filter File", os.getcwd(), "", wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
        dlg.Destroy()

        return file_path
    

class MarketModel:
    def __init__(self):
        self.settings = {
            'endPoints' : make_request(__base_url__, 'application/vnd.ccp.eve.Api-v3+json'),
        }

        self.directory = os.getcwd()
        self.filter_file = 'nofile'

    def get_region(self, event):
        self.set_status_text("Dump beginning.", 0)

        filter_list = {}
        filter_me = False

        if self.filter_file != 'nofile' and os.path.isfile(self.filter_file):
            with open(self.filter_file, 'rb') as filter_file:
                filter_reader = csv.reader(filter_file, dialect='excel')
                for row in filter_reader:
                    filter_list[int(row[0])] = True
            filter_me = True
        item_count = len(self.market_items)
        count = 0
        batch = 0
        start_time = time.time()
        buy_urls = []
        sell_urls = []

        with open(self.directory + '\\orders.csv', 'wb') as csv_file:
            writer = csv.writer(csv_file, dialect='excel')
            writer.writerow([
                'Buy',
                'typeid',
                'volume',
                'issued',
                'duration',
                'Volume Entered',
                'Minimum Volume',
                'range',
                'price',
                'locationid',
                'locationname'
            ])

            for item in self.market_items:
                count += 1
                wx.Yield()

                if filter_me:
                    if int(item['id']) in filter_list:
                        buy_urls.append(self.currentRegion['marketBuyOrders']['href'] + "?type=" + item['href'])
                        sell_urls.append(self.currentRegion['marketSellOrders']['href'] + "?type=" + item['href'])
                        batch += 1
                else:
                        buy_urls.append(self.currentRegion['marketBuyOrders']['href'] + "?type=" + item['href'])
                        sell_urls.append(self.currentRegion['marketSellOrders']['href'] + "?type=" + item['href'])
                        batch += 1

                if (item_count == count) or (batch == 20):
                    buy = make_multiple_requests(buy_urls, 'application/vnd.ccp.eve.MarketOrderCollection-v1+json; charset=utf-8')
                    sell = make_multiple_requests(sell_urls, 'application/vnd.ccp.eve.MarketOrderCollection-v1+json; charset=utf-8')
                    batch = 0
                    now = time.time()
                    so_far = now - start_time
                    fraction = float(count) / float(item_count)
                    total = so_far / fraction
                    remaining = total - so_far
                    self.set_status_text("Completion: " + locale.format("%d", count,grouping=True) + '/' + locale.format("%d", item_count, grouping=True), 0)
                    self.set_status_text(locale.format("%d", so_far, grouping=True) + '/' + locale.format("%d", remaining, grouping=True) + '/' + locale.format("%d", total, grouping=True), 1)
                    wx.Yield()
                    buy_urls = []
                    sell_urls = []

                    for buyitem in buy:
                        writer.writerow([
                            1,
                            buyitem['type']['id'],
                            buyitem['volume'],
                            buyitem['issued'],
                            buyitem['duration'],
                            buyitem['volumeEntered'],
                            buyitem['minVolume'],
                            buyitem['range'],
                            buyitem['price'],
                            buyitem['location']['id'],
                            buyitem['location']['name']
                        ])

                    for sellitem in sell:
                        writer.writerow([
                            0,
                            sellitem['type']['id'],
                            sellitem['volume'],
                            sellitem['issued'],
                            sellitem['duration'],
                            sellitem['volumeEntered'],
                            1,
                            sellitem['range'],
                            sellitem['price'],
                            sellitem['location']['id'],
                            sellitem['location']['name']
                        ])

        self.set_status_text("Complete.", 0)
        self.set_status_text("", 1)
        pub.sendMessage('completedDump', data='done')

    def load_base_data(self):
        self.set_status_text("Loading Regions", 0)
        self.regions = make_request(self.settings['endPoints']['regions']['href'], 'application/vnd.ccp.eve.RegionCollection-v1+json;')

        pub.sendMessage('update_regions')

        self.set_status_text("Loading Market Types", 0)
        self.market_items = self.walk_market_types('application/vnd.ccp.eve.MarketTypeCollection-v1+json; charset=utf-8')
        self.set_status_text("Select a region to continue.", 0)
    
    def walk_market_types(self, accept):
        return_collection = []
        url = self.settings['endPoints']['marketTypes']['href']
        page = 0

        while True:
            page += 1
            self.set_status_text("Loading Market Types:", 0)
            self.set_status_text(str(page), 1)
            wx.Yield()
            walker = make_request(url, accept)

            for item in walker['items']:
                return_collection.append(item['type'])

            if 'next' in walker:
                url = walker['next']['href']

            else:
                break

        self.set_status_text('', 1)

        return return_collection

    @staticmethod
    def set_status_text(data, external_id):
        pub.sendMessage('update_status', data=data, extra1=external_id)


class MarketController:
    def __init__(self, app):
        self.view = MarketView(None, -1, "Market Loader")

        self.view.regionCombo.Bind(wx.EVT_COMBOBOX, self.on_region_select)
        self.view.save.Bind(wx.EVT_BUTTON, self.on_save_dir)
        self.view.filter.Bind(wx.EVT_BUTTON, self.on_filter_file)

        self.view.Show(True)        
        app.SetTopWindow(self.view)
        self.model = MarketModel()
        
        self.view.get_region.Bind(wx.EVT_BUTTON, self.model.get_region)

        pub.subscribe(self.update_status_controller, 'update_status')
        pub.subscribe(self.update_regions_controller, 'update_regions')
        pub.subscribe(self.completed_dump, 'completedDump')

        self.model.load_base_data()

    def on_region_select(self, event):
        selected = self.view.regionCombo.GetClientData(self.view.regionCombo.GetSelection())
        self.model.currentRegion = make_request(selected['href'], 'application/vnd.ccp.eve.Region-v1+json; charset=utf-8')
        self.view.get_region.Enable()
        self.view.SetStatusText("Ready.", 0)

    def on_save_dir(self, event):
        self.model.directory = self.view.show_dir()
    
    def on_filter_file(self, event):
        self.model.filter_file = self.view.select_filter_file()
    
    def update_status_controller(self, data, extra1=0):
        self.view.update_status(data, extra1)

    # TODO: Figure out if this is actually used somewhere
    def get_region_controller(self, event):
        self.view.get_region.Disable()
        self.view.regionCombo.Disable()
        self.model.get_region()
    
    def completed_dump(self, data):
        self.view.get_region.Enable()
        self.view.regionCombo.Enable()

    def update_regions_controller(self):
        self.view.update_regions(self.model.regions)

if __name__ == '__main__':
    app = wx.App(False)
    controller = MarketController(app)     # Create an instance of the application class
    app.MainLoop()                         # Tell it to start processing events
