/* eslint-disable */
if (numphases.active == 1) {
  /* two phases */
  p.x_range.end = 2.01;
} else {
  p.x_range.end = 1.01;
}
const period = parseFloat(textinput.value);
for (let i = 0; i < n_labels; i++) {
  const folda = eval(`folda${i}`).data_source;
  const foldaerr = eval(`foldaerr${i}`).data_source;
  const foldb = eval(`foldb${i}`).data_source;
  const foldberr = eval(`foldberr${i}`).data_source;
  const mjd = folda.data.mjd;
  for (let m = 0; m < mjd.length; m++) {
    folda.data.mjd_folda[m] = (mjd[m] % period) / period;
    foldaerr.data.xs[m] = [folda.data.mjd_folda[m], folda.data.mjd_folda[m]];
    foldb.data.mjd_foldb[m] = folda.data.mjd_folda[m] + 1;
    foldberr.data.xs[m] = [foldb.data.mjd_foldb[m], foldb.data.mjd_foldb[m]];
  }
  folda.change.emit();
  foldaerr.change.emit();
  foldb.change.emit();
  foldberr.change.emit();
}
