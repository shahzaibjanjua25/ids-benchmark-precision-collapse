# NSL-KDD label mapping and mixed-resolution note

The canonical mapping used for the reanalysis is `results/family_mapping.csv`. Both true and predicted labels are mapped with this table. It contains the 40 fine labels in the train/test union; 38 have positive support in the official test split, and 17 of those have no training examples.

| Category | Fine labels |
|---|---|
| Normal | normal |
| DoS | neptune, smurf, back, teardrop, pod, land, apache2, processtable, mailbomb, udpstorm |
| Probe | satan, ipsweep, portsweep, nmap, mscan, saint |
| R2L | warezclient, guess_passwd, warezmaster, imap, ftp_write, multihop, phf, spy, snmpguess, snmpgetattack, httptunnel, named, sendmail, xlock, xsnoop, worm |
| U2R | buffer_overflow, rootkit, loadmodule, perl, ps, xterm, sqlattack |

In the official test split, test-only labels occur in each of the four attack families (DoS, Probe, R2L and U2R). A coherent mixed-resolution score groups the seen and unseen fine labels within any family containing a test-only label, and applies the same grouping to truth and predictions. Since all four attack families are affected, this mixed taxonomy is exactly the five-category mapping above. Thus its positive-support and inferred-union scores are equal: each of the five categories has positive test support, and the mapped truth/prediction union contains no extra category. The five-category reanalysis does not isolate a gain from changing only the 17 unavailable labels; it reports the coherent family-level target required to score those labels consistently.
