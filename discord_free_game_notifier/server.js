const express = require('express');
const app = express();
const axios = require('axios');

app.get('/', (req, res) => {
  axios.get('http://localhost:5000/api')
    .then((response) => {
      res.send(response.data);
    })
    .catch((hata) => {
      console.error(hata);
    });
});

app.listen(3000, () => {
  console.log('Sunucu 3000 portunda çalışıyor');
});
