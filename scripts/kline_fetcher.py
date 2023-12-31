import argparse
import requests
import csv
import os
import glob
import time

from datetime import datetime, timedelta, timezone
from tqdm import tqdm

DURATIONS = {
        "1d": timedelta(days=1),
        "6h": timedelta(hours=6),
        "1h": timedelta(hours=1),
        "30m": timedelta(minutes=30),
        "5m": timedelta(minutes=5),
    }

TIMESTAMP = int(datetime.now().timestamp()*1000000)


def get_klines(symbol, start_time, end_time, interval='1d'):
    url = "https://api.binance.com/api/v3/klines"
    limit = 500  # API limit
    interval_duration = DURATIONS[interval]
    max_duration = limit * interval_duration

    all_data = []

    while start_time < end_time:
        current_end_time = min(start_time + max_duration, end_time)
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(current_end_time.timestamp() * 1000),
            "limit": limit
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if not data:
                break  # Break the loop if no data is returned
            print("URL:", response.request.url)

            all_data.extend(data)

            # Update start_time: Use the close time of the last kline plus 1 millisecond
            last_kline_close_time = data[-1][6]
            start_time = (datetime.utcfromtimestamp((last_kline_close_time + 1) / 1000)).replace(tzinfo=timezone.utc)

            # Safety check to avoid infinite loops
            if current_end_time >= end_time:
                break
        else:
            print(f"Error fetching data for {symbol}: {response.status_code}")
            break

        time.sleep(0.5)  # To respect API rate limits

    return all_data


def save_to_csv(data, symbol, save_folder):
    save_folder = f'{save_folder}/raw/{TIMESTAMP}/'
    os.makedirs(save_folder, exist_ok=True)
    filename = f"{save_folder}/klines_{symbol}.csv"
    
    headers = [
        "symbol", "kline_open_time", "open_price", "high_price", "low_price", 
        "close_price", "volume", "kline_close_time", "quote_asset_volume", 
        "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume"
    ]

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for line in data:
            writer.writerow([symbol] + line[:-1])  # Add symbol and exclude the last element


def concatenate_csv(save_folder):
    save_folder = f'{save_folder}/combined/{TIMESTAMP}/'
    os.makedirs(save_folder, exist_ok=True)
    all_filenames = glob.glob(os.path.join(f'{save_folder}/../../raw/{TIMESTAMP}', "klines_*.csv"))
    combined_csv = os.path.join(save_folder, "klines.csv")

    with open(combined_csv, 'w', newline='') as outfile:
        for i, fname in enumerate(all_filenames):
            with open(fname, 'r') as infile:
                if i != 0:
                    infile.readline()  # Skip the header for all but the first file
                outfile.write(infile.read())

    print(f"Combined CSV file created at {combined_csv}")


def main():
    parser = argparse.ArgumentParser(description="Fetch Kline/Candlestick Data for given symbols")
    parser.add_argument("--symbols", nargs='+', type=str, required=True, help="List of symbols")
    parser.add_argument("--start-date", type=str, required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, required=True, help="End date in YYYY-MM-DD format")
    parser.add_argument("--save-folder", "-sf", type=str, required=True, help="Folder to save output CSV files")
    parser.add_argument("--interval", type=str, required=True, choices=['5m', '30m', '1h', '6h', '1d'], help="Interval for klines")

    args = parser.parse_args()

    # Parsing start and end dates (assuming input dates are in UTC)
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) if args.interval == '5d' else (datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) - DURATIONS[args.interval])
    print(start_date, end_date)

    for symbol in tqdm(args.symbols, desc="Processing symbols"):
        data = get_klines(symbol, start_date, end_date, args.interval)
        if data:
            save_to_csv(data, symbol, args.save_folder)

    print('Almost done - concatenating data')
    concatenate_csv(args.save_folder)

if __name__ == "__main__":
    main()



# python scripts/kline_fetcher.py --interval 5m --start-date 2023-11-01 --end-date 2023-12-01 --save-folder ./data/5m/ --symbols BTCFDUSD BTCUSDT ETHUSDT SOLUSDT JTOUSDT ADAUSDT XRPUSDT AVAXUSDT USDCUSDT ORDIUSDT DOGEUSDT BNBUSDT FDUSDUSDT MATICUSDT LINKUSDT ARBUSDT DOTUSDT OPUSDT MEMEUSDT TIAUSDT LUNCUSDT NEARUSDT USDTTRY JTOTRY FTMUSDT PEPEUSDT ATOMUSDT RUNEUSDT SHIBUSDT FILUSDT GALAUSDT IMXUSDT ETHBTC ALGOUSDT FTTUSDT ETCUSDT LTCUSDT DYDXUSDT BTCTUSD BEAMXUSDT AKROUSDT ETHFDUSD ADABTC UNIUSDT TUSDUSDT SANDUSDT SOLBTC GFTUSDT INJUSDT RNDRUSDT SUIUSDT APTUSDT TRXUSDT QIUSDT USTCUSDT EGLDUSDT STMXUSDT RAYUSDT BUSDUSDT LUNAUSDT UNFIUSDT FETUSDT EOSUSDT WRXUSDT SEIUSDT APEUSDT BAKEUSDT BCHUSDT AVAXTRY FLOWUSDT TRBUSDT BLURUSDT BTCUSDC AAVEUSDT OGUSDT GASUSDT ETHUSDC XRPBTC WLDUSDT ICPUSDT CAKEUSDT AVAXBTC GMTUSDT JOEUSDT CFXUSDT STXUSDT MANAUSDT BNBBTC SUPERUSDT MASKUSDT CHZUSDT XLMUSDT MEMETRY HOOKUSDT SOLBUSD BTTCUSDT LDOUSDT WAVESUSDT GRTUSDT AXSUSDT LUNCTRY HBARUSDT ORDITRY WBTCBTC NEOUSDT AGIXUSDT SNXUSDT IDUSDT VETUSDT CYBERUSDT MKRUSDT MAGICUSDT VITEUSDT SUSHIUSDT SOLFDUSD CTXCUSDT DOTBTC HIGHUSDT ETHBUSD ILVUSDT YFIUSDT XMRUSDT CRVUSDT ZILUSDT MINAUSDT ADATRY NTRNUSDT DOGEBTC ENSUSDT XVSUSDT RDNTUSDT FIDAUSDT PEPETRY ONEUSDT BEAMXTRY KAVAUSDT SCUSDT PYRUSDT COMPUSDT EDUUSDT FLOKIUSDT MATICBTC SLPUSDT LQTYUSDT THETAUSDT ROSEUSDT AUCTIONUSDT SSVUSDT LOOMUSDT YGGUSDT ASTRUSDT CELOUSDT STGUSDT ARKMUSDT SOLETH GMXUSDT FTMBTC IOTAUSDT OGTRY MAVUSDT KLAYUSDT POWRUSDT QNTUSDT XRPTRY 1INCHUSDT BNBFDUSD LINAUSDT USDTBRL DREPUSDT MDTUSDT KSMUSDT KP3RUSDT BETAUSDT CHESSUSDT ETHTUSD AEURUSDT C98USDT BLZUSDT RVNUSDT STORJUSDT HOTUSDT ACHUSDT BELUSDT GLMRUSDT LINKBTC FDUSDBUSD TIATRY BTCTRY QTUMUSDT JASMYUSDT SXPUSDT REEFUSDT SHIBTRY TWTUSDT SOLTRY ENJUSDT USTCTRY HFTUSDT STRAXUSDT ARUSDT
