import xml.etree.ElementTree as ET
from urllib.request import urlopen
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os


class DovizKurlari():
    def __init__(self):
        pass  # Henüz herhangi bir başlangıç değeri yok

    def _veri_update(self, zaman="Bugün"):
        """
        Döviz kurlarını TCMB'nin XML servisinden çekip işler.
        Varsayılan olarak bugünün kurlarını çeker.
        Başka tarih verilirse o tarih için url oluşturulup veriler çekilir.
        """
        try:
            if zaman == "Bugün":
                self.url = "http://www.tcmb.gov.tr/kurlar/today.xml"
            else:
                self.url = zaman  # Burada 'zaman' direkt url olarak kabul edilir

            # XML verisi çekilip parse ediliyor
            tree = ET.parse(urlopen(self.url))
            root = tree.getroot()
            self.son = {}  # Döviz verilerinin tutulacağı sözlük
            self.Kur_Liste = []  # Kodların listesi

            # Her bir döviz için verileri çekip sözlüğe kaydet
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

            return self.son  # Güncellenen veriler döndürülür

        except Exception as e:
            return f"HATA: {e}"  # Hata durumunda mesaj döner

    def DegerSor(self, *sor):
        """
        İstenilen döviz kodu ve istenilen alan (örneğin 'ForexBuying') sorgulanır.
        Eğer parametre verilmezse tüm veriler döner.
        """
        self._veri_update()  # Verileri güncelle
        if not any(sor):
            return self.son
        else:
            return self.son.get(sor[0]).get(sor[1])

    def Arsiv(self, Gun, Ay, Yil, *sor):
        """
        Belirtilen gün, ay, yıl için arşivden veri çeker.
        Tarih doğru değilse veya tatilse hata döner.
        """
        a = self._veri_update(self.__Url_Yap(Gun, Ay, Yil))
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
        """
        Tarih parametresi 'GG.AA.YYYY' formatında beklenir.
        Bu tarih için arşivden veri çeker.
        """
        takvim = Tarih.split(".")
        Gun = takvim[0]
        Ay = takvim[1]
        Yil = takvim[2]
        a = self._veri_update(self.__Url_Yap(Gun, Ay, Yil))
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
        """
        TCMB arşiv URL'sini istenilen gün için oluşturur.
        Gün ve ay tek haneliyse başına 0 ekler.
        """
        if len(str(Gun)) == 1:
            Gun = "0" + str(Gun)
        if len(str(Ay)) == 1:
            Ay = "0" + str(Ay)

        self.url = f"http://www.tcmb.gov.tr/kurlar/{Yil}{Ay}/{Gun}{Ay}{Yil}.xml"
        return self.url


class AdvancedDovizUygulamasi:
    def __init__(self, root):
        self.root = root
        self.theme_mode = "light"  # Varsayılan tema
        self.themes = {
            "light": {
                "bg": "white",
                "fg": "black",
                "top_bg": "#ececec",
                "left_bg": "#f0f0f0",
                "button_bg": "#3B82F6",
                "button_fg": "white",
                "listbox_bg": "white",
                "listbox_fg": "black",
                "entry_bg": "white",
                "entry_fg": "black",
                "frame_bg": "white",
                "label_bg": "white",
                "label_fg": "black",
                "forex_buy": "#a6f0a6",
                "forex_sell": "#f09a9a"
            },
            "dark": {
                "bg": "#2d2d2d",
                "fg": "white",
                "top_bg": "#1e1e1e",
                "left_bg": "#252526",
                "button_bg": "#0d6efd",
                "button_fg": "white",
                "listbox_bg": "#3e3e3e",
                "listbox_fg": "white",
                "entry_bg": "#3e3e3e",
                "entry_fg": "white",
                "frame_bg": "#2d2d2d",
                "label_bg": "#2d2d2d",
                "label_fg": "white",
                "forex_buy": "#2a5c2a",
                "forex_sell": "#5c2a2a"
            }
        }
        
        self.kur = DovizKurlari()
        self.kur._veri_update()  # Döviz verilerini yükle
        
        self.favoriler = set()
        self.favoriler = self.favorileri_yukle()

        # Ana pencere ayarları
        root.title("Döviz Uygulaması")
        root.geometry("1000x600")
        root.minsize(700, 475)

        # Üst çubuk (arama ve ayarlar)
        self.top_frame = tk.Frame(root, bg=self.themes[self.theme_mode]["top_bg"], height=60)
        self.top_frame.pack(side="top", fill="x")

        self.search_var = tk.StringVar()  # Arama kutusu için değişken

        self.app_label = tk.Label(self.top_frame, text="Döviz Takip", 
                                bg=self.themes[self.theme_mode]["top_bg"], 
                                font=("Arial", 16, "bold"))
        self.app_label.pack(side="left", padx=20)

        self.search_entry = tk.Entry(self.top_frame, textvariable=self.search_var, 
                                   font=("Arial", 12), width=40,
                                   bg=self.themes[self.theme_mode]["entry_bg"],
                                   fg=self.themes[self.theme_mode]["entry_fg"])
        self.search_entry.pack(side="left", padx=10, pady=10)

        self.lb = None  # Öneri listesi için listbox değişkeni

        self.search_entry.bind("<KeyRelease>", self.autocomplete_listbox_show)
        self.search_entry.bind("<Return>", lambda event: self.search_currency())  # Enter tuşu

        self.search_button = tk.Button(self.top_frame, text="Ara", 
                                     command=self.search_currency, 
                                     bg=self.themes[self.theme_mode]["button_bg"], 
                                     fg=self.themes[self.theme_mode]["button_fg"])
        self.search_button.pack(side="left", padx=5, pady=10)

        self.settings_button = tk.Button(self.top_frame, text="🌓", font=("Arial", 12),
                                       command=self.toggle_theme)
        self.settings_button.pack(side="right", padx=20)

        # Sol menü (Favoriler, yükselen, düşen kurlar)
        self.left_frame = tk.Frame(root, bg=self.themes[self.theme_mode]["left_bg"], width=180)
        self.left_frame.pack(side="left", fill="y")

        self.fav_button = tk.Button(self.left_frame, text="⭐ Favoriler", width=20, 
                                   command=self.show_favoriler)
        self.fav_button.pack(pady=10)

        self.rising_button = tk.Button(self.left_frame, text="📈 En Çok Yükselen", width=20)
        self.rising_button.pack(pady=10)

        self.falling_button = tk.Button(self.left_frame, text="📉 En Çok Düşen", width=20)
        self.falling_button.pack(pady=10)

        # Ana ekran (arama sonuçları burada gösterilir)
        self.main_frame = tk.Frame(root, bg=self.themes[self.theme_mode]["bg"])
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.main_label = tk.Label(self.main_frame, text="İçerik burada gösterilecek", 
                                 font=("Arial", 14), 
                                 bg=self.themes[self.theme_mode]["bg"],
                                 fg=self.themes[self.theme_mode]["fg"])
        self.main_label.pack(pady=20)

    def toggle_theme(self):
        """Tema değiştirme fonksiyonu"""
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        self.apply_theme()
        
    def apply_theme(self):
        """Tüm widget'lara tema uygula"""
        theme = self.themes[self.theme_mode]
        
        # Ana pencere arka planı
        self.root.config(bg=theme["bg"])
        
        # Üst çerçeve
        self.top_frame.config(bg=theme["top_bg"])
        self.app_label.config(bg=theme["top_bg"], fg=theme["fg"])
        
        # Arama kutusu
        self.search_entry.config(bg=theme["entry_bg"], fg=theme["fg"])
        
        # Butonlar
        self.search_button.config(bg=theme["button_bg"], fg=theme["button_fg"])
        self.settings_button.config(bg=theme["button_bg"], fg=theme["button_fg"])
        
        # Sol menü
        self.left_frame.config(bg=theme["left_bg"])
        for widget in self.left_frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(bg=theme["button_bg"], fg=theme["button_fg"])
        
        # Ana ekran
        self.main_frame.config(bg=theme["bg"])
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, (tk.Label, tk.Frame)):
                widget.config(bg=theme["bg"], fg=theme["fg"])
            elif isinstance(widget, tk.Button):
                widget.config(bg=theme["button_bg"], fg=theme["button_fg"])
        
        # Listbox varsa güncelle
        if self.lb:
            self.lb.config(bg=theme["listbox_bg"], fg=theme["listbox_fg"])
        
        # Favorileri yenile
        if hasattr(self, 'favoriler_gosterildi'):
            self.show_favoriler()

    def search_currency(self):
        query = self.search_var.get().strip().upper()

        # Ana ekranı temizle
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        if self.lb:
            self.lb.destroy()
            self.lb = None

        if query:
            result = self.kur.son.get(query)
            if result:
                title = tk.Label(self.main_frame, 
                                text=f"{result.get('Kod', '')} - {result.get('isim', '')}",
                                font=("Arial", 20, "bold"), 
                                bg=self.themes[self.theme_mode]["bg"],
                                fg=self.themes[self.theme_mode]["fg"])
                title.pack(pady=(20, 10))

                # Forex alış/satış
                forex_frame = tk.Frame(self.main_frame, bg=self.themes[self.theme_mode]["bg"])
                forex_frame.pack(pady=10)

                forex_alış = tk.Label(forex_frame, 
                                    text=f"Forex Alış\n{result.get('ForexBuying', 'N/A')}",
                                    bg=self.themes[self.theme_mode]["forex_buy"], 
                                    fg=self.themes[self.theme_mode]["fg"], 
                                    font=("Arial", 16, "bold"),
                                    width=15, height=4, relief="ridge", bd=2)
                forex_alış.pack(side="left", padx=10)

                forex_satış = tk.Label(forex_frame, 
                                     text=f"Forex Satış\n{result.get('ForexSelling', 'N/A')}",
                                     bg=self.themes[self.theme_mode]["forex_sell"], 
                                     fg=self.themes[self.theme_mode]["fg"], 
                                     font=("Arial", 16, "bold"),
                                     width=15, height=4, relief="ridge", bd=2)
                forex_satış.pack(side="left", padx=10)

                # Banknot alış/satış
                banknot_frame = tk.Frame(self.main_frame, bg=self.themes[self.theme_mode]["bg"])
                banknot_frame.pack(pady=10)

                banknot_alış = tk.Label(banknot_frame, 
                                      text=f"Banknot Alış\n{result.get('BanknoteBuying', 'N/A')}",
                                      bg=self.themes[self.theme_mode]["forex_buy"], 
                                      fg=self.themes[self.theme_mode]["fg"], 
                                      font=("Arial", 16, "bold"),
                                      width=15, height=4, relief="ridge", bd=2)
                banknot_alış.pack(side="left", padx=10)

                banknot_satış = tk.Label(banknot_frame, 
                                       text=f"Banknot Satış\n{result.get('BanknoteSelling', 'N/A')}",
                                       bg=self.themes[self.theme_mode]["forex_sell"], 
                                       fg=self.themes[self.theme_mode]["fg"], 
                                       font=("Arial", 16, "bold"),
                                       width=15, height=4, relief="ridge", bd=2)
                banknot_satış.pack(side="left", padx=10)

                # Favori ekleme butonu
                fav_btn = tk.Button(self.main_frame, text="⭐ Favorilere Ekle", font=("Arial", 12),
                                  command=lambda kod=result.get("Kod"): self.favori_ekle(kod),
                                  bg=self.themes[self.theme_mode]["button_bg"],
                                  fg=self.themes[self.theme_mode]["button_fg"])
                fav_btn.pack(pady=10)

            else:
                tk.Label(self.main_frame, text="Döviz kodu bulunamadı.", fg="red",
                       font=("Arial", 12), 
                       bg=self.themes[self.theme_mode]["bg"]).pack(pady=10)
        else:
            tk.Label(self.main_frame, text="Lütfen arama kutusuna bir şey yazın.", fg="orange",
                   font=("Arial", 12), 
                   bg=self.themes[self.theme_mode]["bg"]).pack(pady=10)

    def show_favoriler(self):
        self.favoriler_gosterildi = True
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        if not self.favoriler:
            tk.Label(self.main_frame, text="Henüz favori eklenmedi.", 
                    font=("Arial", 12), 
                    bg=self.themes[self.theme_mode]["bg"],
                    fg=self.themes[self.theme_mode]["fg"]).pack(pady=20)
            return

        title = tk.Label(self.main_frame, text="⭐ Favori Dövizler", 
                        font=("Arial", 18, "bold"), 
                        bg=self.themes[self.theme_mode]["bg"],
                        fg=self.themes[self.theme_mode]["fg"])
        title.pack(pady=(20, 10))

        for kod in self.favoriler:
            result = self.kur.son.get(kod)
            if result:
                frame = tk.Frame(self.main_frame, 
                                bg=self.themes[self.theme_mode]["bg"], 
                                bd=1, relief="solid")
                frame.pack(padx=20, pady=10, fill="x")

                # Tıklanabilir döviz ismi
                btn = tk.Button(frame, text=f"{kod} - {result.get('isim', '')}",
                               font=("Arial", 14), 
                               bg=self.themes[self.theme_mode]["bg"], 
                               fg=self.themes[self.theme_mode]["fg"],
                               bd=0, anchor="w",
                               command=lambda k=kod: self.show_currency_from_fav(k))
                btn.pack(side="left", padx=10)

                # Alış ve satış birlikte gösteriliyor
                fiyat_alış = result.get('ForexBuying', 'N/A')
                fiyat_satış = result.get('ForexSelling', 'N/A')
                fiyat_label = tk.Label(
                    frame,
                    text=f"Alış: {fiyat_alış} | Satış: {fiyat_satış}",
                    font=("Arial", 12),
                    bg=self.themes[self.theme_mode]["bg"],
                    fg=self.themes[self.theme_mode]["fg"]
                )
                fiyat_label.pack(side="right", padx=10)
    
                # ❌ Kaldır butonu
                remove_btn = tk.Button(frame, text="❌ Kaldır", font=("Arial", 10),
                                     command=lambda k=kod: self.favori_cikar(k),
                                     bg=self.themes[self.theme_mode]["button_bg"],
                                     fg=self.themes[self.theme_mode]["button_fg"])
                remove_btn.pack(side="right", padx=10)

    def favorileri_yukle(self):
        if os.path.exists("favoriler.json"):
            try:
                with open("favoriler.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data)
            except Exception as e:
                print("Favoriler yüklenirken hata:", e)
        return set()

    def favorileri_kaydet(self):
        try:
            with open("favoriler.json", "w", encoding="utf-8") as f:
                json.dump(list(self.favoriler), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Favoriler kaydedilirken hata:", e)
    
    def favori_ekle(self, kod):
        self.favoriler.add(kod)
        self.favorileri_kaydet()
        messagebox.showinfo("Favori Eklendi", f"{kod} favorilere eklendi.")
    
    def favori_cikar(self, kod):
        if kod in self.favoriler:
            self.favoriler.remove(kod)
            self.favorileri_kaydet()  # Favorileri dosyaya kaydet
            self.show_favoriler()      # Favoriler ekranını güncelle
            messagebox.showinfo("Favori Kaldırıldı", f"{kod} favorilerden çıkarıldı.")

    
    def show_currency_from_fav(self, kod):
        # ✅ Favori listesinden tıklanarak detay göster
        self.search_var.set(kod)
        self.search_currency()

    def autocomplete_listbox_show(self, event):
        query = self.search_var.get().strip().upper()

        if not query:
            try:
                if self.topwin.winfo_exists():
                    self.topwin.destroy()
            except AttributeError:
                pass
            return

        try:
            if self.topwin.winfo_exists():
                self.topwin.destroy()
        except AttributeError:
            pass

        matches = [kod for kod in self.kur.Kur_Liste if kod.startswith(query)]
        if not matches:
            return

        # Arama kutusunun konumunu al
        x = self.search_entry.winfo_rootx()
        y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height()
        width = self.search_entry.winfo_width()

        self.topwin = tk.Toplevel(self.search_entry)
        self.topwin.overrideredirect(True)
        self.topwin.geometry(f"{width}x{min(6, len(matches)) * 20}+{x}+{y}")

        self.lb = tk.Listbox(self.topwin, font=("Arial", 11),
                            bg=self.themes[self.theme_mode]["listbox_bg"],
                            fg=self.themes[self.theme_mode]["listbox_fg"])
        self.lb.pack(fill="both", expand=True)

        for item in matches:
            self.lb.insert(tk.END, item)

        self.lb.bind("<<ListboxSelect>>", self.autocomplete_selection)

    def autocomplete_selection(self, event):
        if self.lb:
            selected = self.lb.get(tk.ACTIVE)
            self.search_var.set(selected)
            self.lb.destroy()
            self.lb = None
            self.search_currency()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedDovizUygulamasi(root)
    root.mainloop()