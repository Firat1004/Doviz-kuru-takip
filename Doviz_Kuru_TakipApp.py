import xml.etree.ElementTree as ET
from urllib.request import urlopen
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os
import threading
import time
from plyer import notification
import winsound  # Windows için ses bildirimleri
import pygame   # Diğer platformlar için ses bildirimleri


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

def kur_takip_et(doviz_kodu, hedef_deger, kontrol_tipi="ForexBuying", kontrol_araligi=300):
    kur = DovizKurlari()
    print(f"[Takip Başladı] {doviz_kodu} için {kontrol_tipi} değeri {hedef_deger}'in altına düşünce bildirim yapılacak.")

    while True:
        try:
            deger = kur.DegerSor(doviz_kodu, kontrol_tipi)
            if deger is None or deger == "":
                print("Veri alınamadı, tekrar denenecek...")
            else:
                deger = float(deger.replace(",", "."))
                if deger <= hedef_deger:
                    print(f"\n🔔 BİLDİRİM: {doviz_kodu} için {kontrol_tipi} değeri hedefin altına düştü: {deger}\n")
                    break
                else:
                    print(f"{doviz_kodu} ({kontrol_tipi}): {deger} > hedef ({hedef_deger}), bekleniyor...")
        except Exception as e:
            print(f"Hata oluştu: {e}")
        
        time.sleep(kontrol_araligi)

class DovizAnaliz:
    def __init__(self, veriler):
        self.veriler = veriler

    def en_degerli_10(self):
        liste = []
        for kod, bilgiler in self.veriler.items():
            if bilgiler['ForexBuying'] and bilgiler['Unit']:
                try:
                    kur = float(bilgiler['ForexBuying'].replace(',', '.'))
                    unit = int(bilgiler['Unit'])
                    tl_deger = kur / unit
                    liste.append((kod, bilgiler['CurrencyName'], tl_deger))
                except:
                    continue
        return sorted(liste, key=lambda x: x[2], reverse=True)[:10]

    def en_degersiz_10(self):
        liste = []
        for kod, bilgiler in self.veriler.items():
            if bilgiler['ForexBuying'] and bilgiler['Unit']:
                try:
                    kur = float(bilgiler['ForexBuying'].replace(',', '.'))
                    unit = int(bilgiler['Unit'])
                    tl_deger = kur / unit
                    liste.append((kod, bilgiler['CurrencyName'], tl_deger))
                except:
                    continue
        return sorted(liste, key=lambda x: x[2])[:10]

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
                "button_bg": "#ececec",
                "button_fg": "black",
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
                "button_bg": "#555658",
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
        
        self.notification_settings = {
            "sound_enabled": True,
            "sound_file": "default",  # "default", "custom" veya dosya yolu
            "popup_enabled": True,
            "history_enabled": True,
            "interval": 300  # Kontrol aralığı (saniye)
        }
        self.individual_notifications = {}  # Her döviz için ayrı bildirim ayarları
        
        # Bildirim geçmişi
        self.notification_history = []
        
        # Ses sistemini başlat
        pygame.mixer.init()
        
        # Ayarları yükle
        self.load_settings()


        self.kur = DovizKurlari()
        self.kur._veri_update()  # Döviz verilerini yükle
        
        # ✅ self.analiz oluşturuluyor (veri yüklendikten sonra)
        self.analiz = DovizAnaliz(self.kur.son)

        self.favoriler = set()
        self.favoriler = self.favorileri_yukle()


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
        
        # Sol menü (Favoriler, yükselen, düşen kurlar)
        self.left_frame = tk.Frame(root, bg=self.themes[self.theme_mode]["left_bg"], width=180)
        self.left_frame.pack(side="left", fill="y")

        self.fav_button = tk.Button(self.left_frame, text="⭐ Favoriler", width=20, 
                                   command=self.show_favoriler)
        self.fav_button.pack(pady=10)

        self.rising_button = tk.Button(self.left_frame, text="📈 Yüksek Birim Kurları", width=20)
        self.rising_button.pack(pady=10)

        self.falling_button = tk.Button(self.left_frame, text="📉 Düşük Birim Kurları", width=20)
        self.falling_button.pack(pady=10)

        self.menu_button = tk.Button(self.left_frame, text="🏠 Ana Sayfa", width=20, command=self.show_anasayfa)
        self.menu_button.pack(pady=10)

        # ✅ Butonlara işlev bağlanıyor
        self.rising_button.config(command=self.en_degerli_goster)
        self.falling_button.config(command=self.en_degersiz_goster)

        # Ana ekran (arama sonuçları burada gösterilir)
        self.main_frame = tk.Frame(root, bg=self.themes[self.theme_mode]["bg"])
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.main_label = tk.Label(self.main_frame, text="İçerik burada gösterilecek", 
                                 font=("Arial", 14), 
                                 bg=self.themes[self.theme_mode]["bg"],
                                 fg=self.themes[self.theme_mode]["fg"])
        self.main_label.pack(pady=20)

        # Ayarlar butonunu değiştiriyoruz
        self.settings_frame = tk.Frame(self.top_frame, bg=self.themes[self.theme_mode]["top_bg"])
        self.settings_frame.pack(side="right", padx=10)
        
        self.notif_button = tk.Button(self.settings_frame, text="🔔", font=("Arial", 12),
                                    command=self.show_notification_settings)
        self.notif_button.pack(side="left", padx=5)
        
        self.settings_button = tk.Button(self.settings_frame, text="🌓", font=("Arial", 12),
                                       command=self.toggle_theme)
        self.settings_button.pack(side="left", padx=5)

    def load_settings(self):
        """Kayıtlı ayarları yükler"""
        if os.path.exists("notification_settings.json"):
            try:
                with open("notification_settings.json", "r", encoding="utf-8") as f:
                    self.notification_settings = json.load(f)
            except Exception as e:
                print("Ayarlar yüklenirken hata:", e)
        
        if os.path.exists("individual_notifications.json"):
            try:
                with open("individual_notifications.json", "r", encoding="utf-8") as f:
                    self.individual_notifications = json.load(f)
            except Exception as e:
                print("Bireysel bildirimler yüklenirken hata:", e)
    
    def save_settings(self):
        """Ayarları kaydeder"""
        try:
            with open("notification_settings.json", "w", encoding="utf-8") as f:
                json.dump(self.notification_settings, f, ensure_ascii=False, indent=2)
            
            with open("individual_notifications.json", "w", encoding="utf-8") as f:
                json.dump(self.individual_notifications, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Ayarlar kaydedilirken hata:", e)
    
    def en_degerli_goster(self):
        # Ana ekranı temizle
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        title = tk.Label(self.main_frame, text="📈 Birim başına en değerli para birimleri (TL Bazında)", 
                        font=("Arial", 18, "bold"),
                        bg=self.themes[self.theme_mode]["bg"],
                        fg=self.themes[self.theme_mode]["fg"])
        title.pack(pady=10)

        for kod, isim, deger in self.analiz.en_degerli_10():
            lbl = tk.Label(self.main_frame, text=f"{kod}: {isim} - {deger:.4f} TL",
                        font=("Arial", 14),
                        bg=self.themes[self.theme_mode]["bg"],
                        fg=self.themes[self.theme_mode]["fg"])
            lbl.pack(anchor="w", padx=20)

    def en_degersiz_goster(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        title = tk.Label(self.main_frame, text="📉 Birim başına en değersiz para birimleri (TL Bazında)", 
                        font=("Arial", 18, "bold"),
                        bg=self.themes[self.theme_mode]["bg"],
                        fg=self.themes[self.theme_mode]["fg"])
        title.pack(pady=10)

        for kod, isim, deger in self.analiz.en_degersiz_10():
            lbl = tk.Label(self.main_frame, text=f"{kod}: {isim} - {deger:.4f} TL",
                        font=("Arial", 14),
                        bg=self.themes[self.theme_mode]["bg"],
                        fg=self.themes[self.theme_mode]["fg"])
            lbl.pack(anchor="w", padx=20)

    def show_anasayfa(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.main_label = tk.Label(self.main_frame, text="İçerik burada gösterilecek", 
                                font=("Arial", 14), 
                                bg=self.themes[self.theme_mode]["bg"],
                                fg=self.themes[self.theme_mode]["fg"])
        self.main_label.pack(pady=20)



    def select_custom_sound(self):
        """Özel ses dosyası seçmek için dosya iletişim kutusu açar"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Ses Dosyası Seç",
            filetypes=[("WAV Dosyaları", "*.wav"), ("Tüm Dosyalar", "*.*")]
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy(file_path, "notification.wav")
                self.notification_settings["sound_file"] = "custom"
                self.save_settings()
                messagebox.showinfo("Başarılı", "Özel ses dosyası başarıyla ayarlandı!")
            except Exception as e:
                messagebox.showerror("Hata", f"Ses dosyası yüklenirken hata oluştu: {e}")

        def update_sound_type(self):
            """Ses tipi güncellendiğinde çalışır"""
        self.notification_settings["sound_file"] = self.sound_type_var.get()
        self.save_settings()  

    def show_notification_settings(self):
        """Genel bildirim ayarları penceresini gösterir"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Bildirim Ayarları")
        settings_win.geometry("500x400")    

        # Ses Ayarları
        sound_frame = tk.LabelFrame(settings_win, text="Ses Ayarları", padx=10, pady=10)
        sound_frame.pack(fill="x", padx=10, pady=5)
        
        
        # Ses seçenekleri
        sound_options_frame = tk.Frame(sound_frame)
        sound_options_frame.pack(fill="x", padx=20, pady=5)
        
        self.sound_type_var = tk.StringVar(value=self.notification_settings["sound_file"])
        
        tk.Radiobutton(sound_options_frame, text="Varsayılan", variable=self.sound_type_var, 
                      value="default", command=self.update_sound_type).pack(anchor="w")
        tk.Radiobutton(sound_options_frame, text="Özel Ses", variable=self.sound_type_var, 
                      value="custom", command=self.update_sound_type).pack(anchor="w")
        
        # Özel ses dosyası seçme butonu
        self.custom_sound_button = tk.Button(sound_options_frame, text="Ses Dosyası Seç",
                                             command=self.select_custom_sound)
        self.custom_sound_button.pack(anchor="w", pady=5)

        # Popup Ayarları
        popup_frame = tk.LabelFrame(settings_win, text="Popup Ayarları", padx=10, pady=10)
        popup_frame.pack(fill="x", padx=10, pady=5)
        
        self.popup_var = tk.BooleanVar(value=self.notification_settings["popup_enabled"])
        popup_cb = tk.Checkbutton(popup_frame, text="Masaüstü bildirimi göster", 
                                 variable=self.popup_var,
                                 command=lambda: self.update_setting("popup_enabled", self.popup_var.get()))
        popup_cb.pack(anchor="w")
        
        # Kontrol Aralığı
        interval_frame = tk.LabelFrame(settings_win, text="Kontrol Aralığı (saniye)", padx=10, pady=10)
        interval_frame.pack(fill="x", padx=10, pady=5)
        
        self.interval_var = tk.IntVar(value=self.notification_settings["interval"])
        interval_spin = tk.Spinbox(interval_frame, from_=60, to=3600, increment=60,
                                 textvariable=self.interval_var,
                                 command=lambda: self.update_setting("interval", self.interval_var.get()))
        interval_spin.pack(anchor="w")
        
        # Bildirim Geçmişi
        history_frame = tk.LabelFrame(settings_win, text="Bildirim Geçmişi", padx=10, pady=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        history_scroll = tk.Scrollbar(history_frame)
        history_scroll.pack(side="right", fill="y")
        
        self.history_list = tk.Listbox(history_frame, yscrollcommand=history_scroll.set)
        self.history_list.pack(fill="both", expand=True)
        
        history_scroll.config(command=self.history_list.yview)
        
        # Geçmişi doldur
        for notif in self.notification_history[-20:]:  # Son 20 bildirimi göster
            self.history_list.insert(tk.END, notif)

    def update_setting(self, key, value):
        """Ayarları günceller"""
        self.notification_settings[key] = value
        self.save_settings()
    
    def update_sound_type(self):
        """Ses tipini günceller"""
        self.notification_settings["sound_file"] = self.sound_type_var.get()
        self.save_settings()
    
    def send_notification(self, title, message):
        """Bildirim gönderir"""
        # Geçmişe ekle
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        notif_text = f"{timestamp} - {title}: {message}"
        self.notification_history.append(notif_text)
        
        # Masaüstü bildirimi
        if self.notification_settings["popup_enabled"]:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="Döviz Takip",
                    timeout=10
                )
            except Exception as e:
                print("Bildirim gönderilirken hata:", e)
        
        # Sesli bildirim
        if self.notification_settings["sound_enabled"]:
            self.play_notification_sound()
    
    def play_notification_sound(self):
        """Bildirim sesini çalar"""
        sound_type = self.notification_settings["sound_file"]
        
        try:
            if sound_type == "default":
                # Windows için varsayılan ses
                winsound.Beep(1000, 500)  # Frekans: 1000Hz, Süre: 500ms
            elif sound_type == "custom" and os.path.exists("notification.wav"):
                # Özel ses dosyası
                pygame.mixer.music.load("notification.wav")
                pygame.mixer.music.play()
        except Exception as e:
            print("Ses çalınırken hata:", e)

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

                # Favori ekleme/kaldırma butonu - DEĞİŞTİRİLDİ
                fav_button_text = "❌ Favoriyi Kaldır" if result.get("Kod") in self.favoriler else "⭐ Favorilere Ekle"
                self.fav_btn = tk.Button(self.main_frame, text=fav_button_text, font=("Arial", 12),
                                    command=lambda kod=result.get("Kod"): self.toggle_favori(kod),
                                    bg=self.themes[self.theme_mode]["button_bg"],
                                    fg=self.themes[self.theme_mode]["button_fg"])
                self.fav_btn.pack(pady=10)

                # Bildirim ayarları bölümü ekliyoruz
                notif_frame = tk.LabelFrame(self.main_frame, text="Bildirim Ayarları", 
                                        padx=10, pady=10,
                                        bg=self.themes[self.theme_mode]["bg"],
                                        fg=self.themes[self.theme_mode]["fg"])
                notif_frame.pack(pady=10, fill="x", padx=20)
                
                # Döviz kodunu al
                kod = result.get("Kod", "")
                
                # Bu döviz için kayıtlı ayarları yükle (yoksa varsayılan oluştur)
                if kod not in self.individual_notifications:
                    self.individual_notifications[kod] = {
                        "enabled": False,
                        "target_type": "ForexBuying",
                        "target_value": "",
                        "condition": "below"  # "below" veya "above"
                    }
                
                #YENİ KOD (Doğrudan aktif kabul edilecek):
                self.individual_notifications[kod]["enabled"] = True  # Otomatik aktif
                
                # Hedef türü seçimi
                tk.Label(notif_frame, text="Hedef Türü:", 
                        bg=self.themes[self.theme_mode]["bg"],
                        fg=self.themes[self.theme_mode]["fg"]).grid(row=1, column=0, sticky="w")
                
                self.target_type_var = tk.StringVar(value=self.individual_notifications[kod]["target_type"])
                target_type_menu = ttk.Combobox(notif_frame, textvariable=self.target_type_var, 
                                            values=["ForexBuying", "ForexSelling", "BanknoteBuying", "BanknoteSelling"])
                target_type_menu.grid(row=1, column=1, sticky="ew", padx=5)
                target_type_menu.bind("<<ComboboxSelected>>", 
                                lambda e: self.update_individual_notif(kod, "target_type", self.target_type_var.get()))
                
                # Koşul seçimi
                self.condition_var = tk.StringVar(value=self.individual_notifications[kod]["condition"])
                condition_menu = ttk.Combobox(notif_frame, textvariable=self.condition_var, 
                                            values=["below", "above"])
                condition_menu.grid(row=1, column=2, sticky="ew", padx=5)
                condition_menu.bind("<<ComboboxSelected>>", 
                                lambda e: self.update_individual_notif(kod, "condition", self.condition_var.get()))
                
                # Hedef değer girişi
                tk.Label(notif_frame, text="Hedef Değer:", 
                        bg=self.themes[self.theme_mode]["bg"],
                        fg=self.themes[self.theme_mode]["fg"]).grid(row=2, column=0, sticky="w")
                
                self.target_value_var = tk.StringVar(value=self.individual_notifications[kod]["target_value"])
                target_value_entry = tk.Entry(notif_frame, textvariable=self.target_value_var,
                                        bg=self.themes[self.theme_mode]["entry_bg"],
                                        fg=self.themes[self.theme_mode]["entry_fg"])
                target_value_entry.grid(row=2, column=1, sticky="ew", padx=5)
                target_value_entry.bind("<FocusOut>", 
                                    lambda e: self.update_individual_notif(kod, "target_value", self.target_value_var.get()))
                
                # Başlat/Durdur butonu
                notif_button = tk.Button(notif_frame, 
                                        text="Takibi Başlat" if not self.individual_notifications[kod].get("running", False) else "Takibi Durdur",
                                        command=lambda: self.toggle_currency_tracking(kod),
                                        bg=self.themes[self.theme_mode]["button_bg"],
                                        fg=self.themes[self.theme_mode]["button_fg"])
                notif_button.grid(row=2, column=2, sticky="ew", padx=5)    

            else:
                tk.Label(self.main_frame, text="Döviz kodu bulunamadı.", fg="red",
                       font=("Arial", 12), 
                       bg=self.themes[self.theme_mode]["bg"]).pack(pady=10)
        else:
            tk.Label(self.main_frame, text="Lütfen arama kutusuna bir şey yazın.", fg="orange",
                   font=("Arial", 12), 
                   bg=self.themes[self.theme_mode]["bg"]).pack(pady=10)

    def update_individual_notif(self, kod, key, value):
        """Sadece hedef değer/tür güncellemesi için"""
        if key != "enabled":  # enabled kontrolünü kaldırıyoruz
            self.individual_notifications[kod][key] = value
            self.save_settings()
    
    def toggle_currency_tracking(self, kod):
        if kod not in self.individual_notifications:
            return
        
        settings = self.individual_notifications[kod]
        settings["enabled"] = True  # Her zaman aktif
        
        if settings.get("running", False):
            settings["running"] = False
            messagebox.showinfo("Bilgi", f"{kod} takibi durduruldu.")
        else:
            try:
                target_value = float(settings["target_value"].replace(",", "."))
                settings["running"] = True
                thread = threading.Thread(
                    target=self.track_currency_thread,
                    args=(kod, settings["target_type"], target_value, settings["condition"]),
                    daemon=True
                )
                thread.start()
                messagebox.showinfo("Bilgi", f"{kod} takibi başlatıldı...")
            except ValueError:
                messagebox.showerror("Hata", "Geçerli bir hedef değer girin!")
            
        self.save_settings()
        self.search_currency()  # Ekranı yenile
    
    def track_currency_thread(self, kod, target_type, target_value, condition):
        """Döviz takibini yapan thread fonksiyonu"""
        kur = DovizKurlari()
        interval = self.notification_settings["interval"]
        
        while kod in self.individual_notifications and self.individual_notifications[kod].get("running", False):
            try:
                result = kur.DegerSor(kod, target_type)
                if result and result != "":
                    current_value = float(result.replace(",", "."))
                    
                    # Koşulu kontrol et
                    if (condition == "below" and current_value <= target_value) or \
                       (condition == "above" and current_value >= target_value):
                        # Bildirim gönder
                        title = f"Döviz Uyarısı: {kod}"
                        message = f"{target_type} değeri {target_value} {'altına' if condition == 'below' else 'üstüne'} düştü: {current_value}"
                        self.send_notification(title, message)
                        
                        # Tekrar bildirim göndermemek için bir süre beklet
                        time.sleep(interval * 2)  # Normal aralığın 2 katı
                        continue
                
                # Bekleme süresi
                time.sleep(interval)
            except Exception as e:
                print(f"Takip sırasında hata: {e}")
                time.sleep(interval)

    def toggle_favori(self, kod):
        """Favori ekleme/kaldırma işlemini tek butonla yönetir"""
        if kod in self.favoriler:
            self.favori_cikar(kod)
        else:
            self.favori_ekle(kod)

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
        # Buton metnini güncelle
        if hasattr(self, 'fav_btn'):
            self.fav_btn.config(text="❌ Favoriyi Kaldır")
        # Favoriler ekranını güncelle
        if hasattr(self, 'favoriler_gosterildi'):
            self.show_favoriler()
    
    def favori_cikar(self, kod):
        if kod in self.favoriler:
            self.favoriler.remove(kod)
            self.favorileri_kaydet()
            messagebox.showinfo("Favori Kaldırıldı", f"{kod} favorilerden çıkarıldı.")
            # Buton metnini güncelle
            if hasattr(self, 'fav_btn'):
                self.fav_btn.config(text="⭐ Favorilere Ekle")
            # Favoriler ekranını güncelle
            if hasattr(self, 'favoriler_gosterildi'):
                self.show_favoriler()
    
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

# Kullanıcı bilgileri (gerçek uygulamada veritabanı veya şifreli dosyada saklanmalı)
VALID_USERNAME = "admin"
VALID_PASSWORD = "12345"

class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Giriş Yap")
        master.geometry("300x200")
        master.resizable(False, False)
        
        # Merkezlemek için
        window_width = master.winfo_reqwidth()
        window_height = master.winfo_reqheight()
        position_right = int(master.winfo_screenwidth()/2 - window_width/2 - 150)
        position_down = int(master.winfo_screenheight()/2 - window_height/2 - 100)
        master.geometry(f"+{position_right}+{position_down}")
        
        # Widget'lar
        self.label = tk.Label(master, text="Lütfen Giriş Yapın", font=("Arial", 14))
        self.label.pack(pady=10)
        
        self.username_label = tk.Label(master, text="Kullanıcı Adı:")
        self.username_label.pack()
        
        self.username_entry = tk.Entry(master)
        self.username_entry.pack(pady=5)
        
        self.password_label = tk.Label(master, text="Şifre:")
        self.password_label.pack()
        
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.pack(pady=5)
        
        self.login_button = tk.Button(master, text="Giriş Yap", command=self.check_credentials)
        self.login_button.pack(pady=10)
        
        # Enter tuşu ile giriş yapma
        master.bind('<Return>', lambda event: self.check_credentials())
    
    def check_credentials(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            self.master.destroy()  # Giriş penceresini kapat
            self.open_main_app()  # Ana uygulamayı başlat
        else:
            messagebox.showerror("Hata", "Geçersiz kullanıcı adı veya şifre!")
            self.password_entry.delete(0, tk.END)  # Şifreyi temizle
    
    def open_main_app(self):
        # Ana uygulamayı başlat
        root = tk.Tk()
        app = AdvancedDovizUygulamasi(root)
        root.mainloop()

# İlk olarak giriş penceresini başlat
login_root = tk.Tk()
login_app = LoginWindow(login_root)
login_root.mainloop()