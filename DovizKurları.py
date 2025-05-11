import xml.etree.ElementTree as ET
from urllib.request import urlopen

class DovizKurları():
    def __init__(self):
        pass

    def __veri_update(self, zaman="Bugün"):
        try:
            if zaman == "Bugün":
                self.url = "http://www.tcmb.gov.tr/kurlar/today.xml"
            else:
                self.url = zaman

            tree = ET.parse(urlopen(self.url))
            root = tree.getroot()
            self.son = {}
            self.Kur_Liste = []

            for kurlars in root.findall('Currency'):
                Kod = kurlars.get('Kod')
                Unit = kurlars.find('Unit').text
                isim = kurlars.find('Isim').text
                CurrencyName = kurlars.find('CurrencyName').text
                ForexBuying = kurlars.find('ForexBuying').text
                ForexSelling = kurlars.find('ForexSelling').text
                BanknoteBuying = kurlars.find('BanknoteBuying').text
                BanknoteSelling = kurlars.find('BanknoteSelling').text
                CrossRateUSD = kurlars.find('CrossRateUSD').text

                self.Kur_Liste.append(Kod)
                self.son[Kod] = {
                    "Kod": Kod,
                    "isim": isim,
                    "CurrencyName": CurrencyName,
                    "Unit": Unit,
                    "ForexBuying": ForexBuying,
                    "ForexSelling": ForexSelling,
                    "BanknoteBuying": BanknoteBuying,
                    "BanknoteSelling": BanknoteSelling,
                    "CrossRateUSD": CrossRateUSD
                }

            return self.son

        except Exception as e:
            return f"HATA: {e}"

    def DegerSor(self, *sor):
        self.__veri_update()
        if not any(sor):
            return self.son
        else:
            return self.son.get(sor[0]).get(sor[1])

    def Arsiv(self, Gun, Ay, Yil, *sor):
        a = self.__veri_update(self.__Url_Yap(Gun, Ay, Yil))
        if not any(sor):
            if a == "HATA":
                return {"Hata": "Tatil günü"}
            return self.son
        else:
            if a == "HATA":
                return "Tatil günü"
            else:
                return self.son.get(sor[0]).get(sor[1])

    def Arsiv_Tarih(self, Tarih="", *sor):
        takvim = Tarih.split(".")
        Gun = takvim[0]
        Ay = takvim[1]
        Yil = takvim[2]
        a = self.__veri_update(self.__Url_Yap(Gun, Ay, Yil))
        if not any(sor):
            if a == "HATA":
                return {"Hata": "Tatil günü"}
            return self.son
        else:
            if a == "HATA":
                return "Tatil günü"
            else:
                return self.son.get(sor[0]).get(sor[1])

    def __Url_Yap(self, Gun, Ay, Yil):
        if len(str(Gun)) == 1:
            Gun = "0" + str(Gun)
        if len(str(Ay)) == 1:
            Ay = "0" + str(Ay)

        self.url = f"http://www.tcmb.gov.tr/kurlar/{Yil}{Ay}/{Gun}{Ay}{Yil}.xml"
        return self.url