import urllib.request

# URL-адрес, на который отправляется запрос
url = "http://127.0.0.1:8000"

# Отправляем GET-запрос на сервер
with urllib.request.urlopen(url) as response:

	# Получаем ответ сервера и выводим его содержимое
	print(response.read().decode('utf-8'))