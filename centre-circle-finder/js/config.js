/* ============================================================
   Centre Circle Finder — monetisation / outbound-link config
   ------------------------------------------------------------
   These URL templates power the "Hotels" and "Transit" buttons
   on every club card. They are plain, unaffiliated links by
   default — append your affiliate / partner parameters here and
   every card on the site picks them up automatically.

   Placeholders (URL-encoded before substitution):
     {q}    → town / place name
     {lat}  → ground latitude
     {lng}  → ground longitude

   Examples:
     Booking.com affiliate:  ...searchresults.html?ss={q}&aid=YOUR_AID
     Trainline / other partners: swap the whole template.
   ============================================================ */
window.CCF_LINKS = {
  hotels: "https://www.booking.com/searchresults.html?ss={q}",
  transit: "https://www.google.com/maps/dir/?api=1&destination={lat}%2C{lng}&travelmode=transit"
};
